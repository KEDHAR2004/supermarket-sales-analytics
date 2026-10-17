import copy
import json
import os
import unittest
from unittest.mock import Mock, patch
from receipts import generate, validate, object_key
import lambda_function

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.r = generate(1)[0]
    def test_deterministic_valid_generator(self):
        self.assertEqual(generate(20), generate(20))
        for r in generate(100):
            validate(r)
    def test_bad_amounts(self):
        for bad in ("NaN", "Infinity", "-1.00", "1.001", 1.5):
            r = copy.deepcopy(self.r)
            r['items'][0]['unit_price_gbp'] = bad
            with self.assertRaises(ValueError):
                validate(r)
    def test_mismatch_and_path_injection(self):
        for field,value in [('total_gbp','999.00'), ('store_id','../../x'), ('receipt_id','a/b'), ('purchased_at','2026-10-17T12:00:00')]:
            r = dict(self.r, **{field:value})
            with self.assertRaises(ValueError):
                validate(r)
    def test_fractional_and_boolean_quantities(self):
        for q in (True, 1.2, 0, -1):
            r = copy.deepcopy(self.r)
            r['items'][0]['quantity'] = q
            with self.assertRaises(ValueError):
                validate(r)
    def test_partial_failure_and_repeat_delivery(self):
        s3 = Mock()
        event = {'Records':[{'messageId':'ok','body':json.dumps(self.r)}, {'messageId':'bad','body':'broken'}]}
        with patch.object(lambda_function, 'get_s3', return_value=s3), patch.dict(os.environ, BUCKET_NAME='test'):
            self.assertEqual(lambda_function.handler(event,None), {'batchItemFailures':[{'itemIdentifier':'bad'}]})
            lambda_function.handler({'Records':event['Records'][:1]},None)
        keys = [c.kwargs['Key'] for c in s3.put_object.call_args_list]
        self.assertEqual(keys, [object_key(self.r)]*2)
    def test_s3_failure_is_retried(self):
        s3 = Mock()
        s3.put_object.side_effect = RuntimeError('offline')
        with patch.object(lambda_function, 'get_s3', return_value=s3), patch.dict(os.environ, BUCKET_NAME='test'):
            result = lambda_function.handler({'Records':[{'messageId':'x','body':json.dumps(self.r)}]}, None)
        self.assertEqual(result, {'batchItemFailures':[{'itemIdentifier':'x'}]})
if __name__ == '__main__':
    unittest.main()
