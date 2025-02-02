import numpy as np
import pytest
import tensorflow as tf

from keras_core import backend
from keras_core import layers
from keras_core import testing


class HashedCrossingTest(testing.TestCase):
    def test_basics(self):
        self.run_layer_test(
            layers.HashedCrossing,
            init_kwargs={
                "num_bins": 3,
                "output_mode": "int",
            },
            input_data=([1, 2], [4, 5]),
            expected_output_shape=(2,),
            expected_num_trainable_weights=0,
            expected_num_non_trainable_weights=0,
            expected_num_seed_generators=0,
            expected_num_losses=0,
            supports_masking=False,
            run_training_check=False,
        )
        self.run_layer_test(
            layers.HashedCrossing,
            init_kwargs={"num_bins": 4, "output_mode": "one_hot"},
            input_data=([1, 2], [4, 5]),
            expected_output_shape=(2, 4),
            expected_num_trainable_weights=0,
            expected_num_non_trainable_weights=0,
            expected_num_seed_generators=0,
            expected_num_losses=0,
            supports_masking=False,
            run_training_check=False,
        )

    def test_correctness(self):
        layer = layers.HashedCrossing(num_bins=5)
        feat1 = np.array(["A", "B", "A", "B", "A"])
        feat2 = np.array([101, 101, 101, 102, 102])
        output = layer((feat1, feat2))
        self.assertAllClose(tf.constant([1, 4, 1, 1, 3]), output)

        layer = layers.HashedCrossing(num_bins=5, output_mode="one_hot")
        feat1 = np.array(["A", "B", "A", "B", "A"])
        feat2 = np.array([101, 101, 101, 102, 102])
        output = layer((feat1, feat2))
        self.assertAllClose(
            np.array(
                [
                    [0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0],
                ]
            ),
            output,
        )

    def test_tf_data_compatibility(self):
        layer = layers.HashedCrossing(num_bins=5)
        feat1 = np.array(["A", "B", "A", "B", "A"])
        feat2 = np.array([101, 101, 101, 102, 102])
        ds = (
            tf.data.Dataset.from_tensor_slices((feat1, feat2))
            .batch(5)
            .map(lambda x1, x2: layer((x1, x2)))
        )
        for output in ds.take(1):
            output = output.numpy()
        self.assertAllClose(np.array([1, 4, 1, 1, 3]), output)

    def test_upsupported_shape_input_fails(self):
        with self.assertRaisesRegex(ValueError, "inputs should have shape"):
            layers.HashedCrossing(num_bins=10)(
                (np.array([[[1.0]]]), np.array([[[1.0]]]))
            )

    @pytest.mark.xfail
    def test_cross_output_dtype(self):
        input_1, input_2 = np.array([1]), np.array([1])

        layer = layers.HashedCrossing(num_bins=2)
        output_dtype = backend.standardize_dtype(
            layer((input_1, input_2)).dtype
        )
        self.assertEqual(output_dtype, "int64")
        layer = layers.HashedCrossing(num_bins=2, dtype="int32")
        output_dtype = backend.standardize_dtype(
            layer((input_1, input_2)).dtype
        )
        self.assertEqual(output_dtype, "int32")
        layer = layers.HashedCrossing(num_bins=2, output_mode="one_hot")
        output_dtype = backend.standardize_dtype(
            layer((input_1, input_2)).dtype
        )
        self.assertEqual(output_dtype, "float32")
        layer = layers.HashedCrossing(
            num_bins=2, output_mode="one_hot", dtype="float64"
        )
        output_dtype = backend.standardize_dtype(
            layer((input_1, input_2)).dtype
        )
        self.assertEqual(output_dtype, "float64")

    def test_non_list_input_fails(self):
        with self.assertRaisesRegex(ValueError, "should be called on a list"):
            layers.HashedCrossing(num_bins=10)(np.array(1))

    def test_single_input_fails(self):
        with self.assertRaisesRegex(ValueError, "at least two inputs"):
            layers.HashedCrossing(num_bins=10)([np.array(1)])

    @pytest.mark.skipif(
        backend.backend() != "tensorflow",
        reason="Need sparse tensor support.",
    )
    def test_sparse_input_fails(self):
        with self.assertRaisesRegex(
            ValueError, "inputs should be dense tensors"
        ):
            sparse_in = tf.sparse.from_dense(np.array([1]))
            layers.HashedCrossing(num_bins=10)((sparse_in, sparse_in))

    def test_float_input_fails(self):
        with self.assertRaisesRegex(
            ValueError, "should have an integer or string"
        ):
            layers.HashedCrossing(num_bins=10)(
                (np.array([1.0]), np.array([1.0]))
            )

    @pytest.mark.skipif(
        backend.backend() != "tensorflow",
        reason="Need string tensor support.",
    )
    def test_tf_string(self):
        layer = layers.HashedCrossing(num_bins=10)
        feat1 = tf.constant("A")
        feat2 = tf.constant(101)
        outputs = layer((feat1, feat2))
        self.assertAllClose(outputs, 1)

        layer = layers.HashedCrossing(num_bins=5, output_mode="one_hot")
        feat1 = tf.constant(["A", "B", "A", "B", "A"])
        feat2 = tf.constant([101, 101, 101, 102, 102])
        self.assertAllClose(
            tf.constant(
                [
                    [0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0],
                ]
            ),
            layer((feat1, feat2)),
        )

        layer = layers.HashedCrossing(num_bins=5)
        feat1 = tf.constant(["A", "B", "A", "B", "A"])
        feat2 = tf.constant([101, 101, 101, 102, 102])
        self.assertAllClose(tf.constant([1, 4, 1, 1, 3]), layer((feat1, feat2)))

        layer = layers.HashedCrossing(
            num_bins=5, output_mode="one_hot", sparse=True
        )
        cloned_layer = layers.HashedCrossing.from_config(layer.get_config())
        feat1 = tf.constant([["A"], ["B"], ["A"], ["B"], ["A"]])
        feat2 = tf.constant([[101], [101], [101], [102], [102]])
        original_outputs = layer((feat1, feat2))
        cloned_outputs = cloned_layer((feat1, feat2))
        self.assertAllClose(
            tf.sparse.to_dense(cloned_outputs),
            tf.sparse.to_dense(original_outputs),
        )
