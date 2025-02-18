# Copyright 2021, The TensorFlow Federated Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import tensorflow as tf

from tensorflow_federated.python.core.impl.execution_contexts import async_execution_context
from tensorflow_federated.python.core.impl.executors import executors_errors


class RetryableErrorTest(tf.test.TestCase):

  def test_is_retryable_error(self):
    retryable_error = executors_errors.RetryableError()
    self.assertTrue(
        async_execution_context._is_retryable_error(retryable_error))
    self.assertFalse(async_execution_context._is_retryable_error(TypeError()))
    self.assertFalse(async_execution_context._is_retryable_error(1))
    self.assertFalse(async_execution_context._is_retryable_error('a'))
    self.assertFalse(async_execution_context._is_retryable_error(None))


class UnwrapValueTest(tf.test.TestCase):

  def test_tensor(self):
    result = async_execution_context._unwrap(tf.constant(1))
    self.assertIsInstance(result, np.int32)
    result = async_execution_context._unwrap(tf.constant([1, 2]))
    self.assertIsInstance(result, np.ndarray)
    self.assertAllEqual(result, [1, 2])

  def test_structure_of_tensors(self):
    result = async_execution_context._unwrap([tf.constant(x) for x in range(5)])
    self.assertIsInstance(result, list)
    for x in range(5):
      self.assertIsInstance(result[x], np.int32)
      self.assertEqual(result[x], x)


if __name__ == '__main__':
  tf.test.main()
