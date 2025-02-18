# Copyright 2018, The TensorFlow Federated Authors.
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
"""Utility methods for working with TensorFlow Federated Model objects."""

import collections
from typing import Callable, Union

import attr
import tensorflow as tf

from tensorflow_federated.python.common_libs import py_typecheck
from tensorflow_federated.python.common_libs import structure
from tensorflow_federated.python.core.impl.types import computation_types
from tensorflow_federated.python.core.impl.types import type_analysis
from tensorflow_federated.python.core.impl.types import type_conversions
from tensorflow_federated.python.learning import model as model_lib


@attr.s(eq=False, frozen=True, slots=True)
class ModelWeights(object):
  """A container for the trainable and non-trainable variables of a `Model`.

  Note this does not include the model's local variables.

  It may also be used to hold other values that are parallel to these variables,
  e.g., tensors corresponding to variable values, or updates to model variables.
  """
  trainable = attr.ib()
  non_trainable = attr.ib()

  @classmethod
  def from_model(cls, model):
    py_typecheck.check_type(model, (model_lib.Model, tf.keras.Model))
    return cls(model.trainable_variables, model.non_trainable_variables)

  @classmethod
  def from_tff_result(cls, struct):
    py_typecheck.check_type(struct, structure.Struct)
    return cls(
        [value for _, value in structure.iter_elements(struct.trainable)],
        [value for _, value in structure.iter_elements(struct.non_trainable)])

  def assign_weights_to(self, model):
    """Assign these TFF model weights to the weights of a model.

    Args:
      model: A `tf.keras.Model` or `tff.learning.Model` instance to assign the
        weights to.
    """
    py_typecheck.check_type(model, (model_lib.Model, tf.keras.Model))
    if isinstance(model, tf.keras.Model):
      tf.nest.map_structure(lambda var, t: var.assign(t),
                            model.trainable_weights, self.trainable)
      tf.nest.map_structure(lambda var, t: var.assign(t),
                            model.non_trainable_weights, self.non_trainable)
    else:
      tf.nest.map_structure(lambda var, t: var.assign(t),
                            model.trainable_variables, self.trainable)
      tf.nest.map_structure(lambda var, t: var.assign(t),
                            model.non_trainable_variables, self.non_trainable)


def weights_type_from_model(
    model: Union[model_lib.Model, Callable[[], model_lib.Model]]
) -> computation_types.StructType:
  """Creates a `tff.Type` from a `tff.learning.Model` or callable that constructs a model.

  Args:
    model: A `tff.learning.Model` instance, or a no-arg callable that returns a
      model.

  Returns:
    A `tff.StructType` representing the TFF type of the `ModelWeights`
    structure for `model`.
  """
  if callable(model):
    # Wrap model construction in a graph to avoid polluting the global context
    # with variables created for this model.
    with tf.Graph().as_default():
      model = model()
  py_typecheck.check_type(model, model_lib.Model)
  return type_conversions.type_from_tensors(ModelWeights.from_model(model))


def parameter_count_from_model(
    model: Union[model_lib.Model, Callable[[], model_lib.Model]]
) -> collections.OrderedDict:
  """Computes count of trainable parameters for a `model`."""
  weights_type = weights_type_from_model(model)
  trainable_weights_type = weights_type.trainable
  tensors_and_params = type_analysis.count_tensors_in_type(
      trainable_weights_type)
  return tensors_and_params
