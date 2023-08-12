from keras_core import backend
from keras_core.api_export import keras_core_export
from keras_core.backend.common import global_state


@keras_core_export("keras_core.random.SeedGenerator")
class SeedGenerator:
    """Generates variable seeds upon each call to a RNG-using function.

    In Keras, all RNG-using methods (such as `keras_core.random.normal()`)
    are stateless, meaning that if you pass an integer seed to them
    (such as `seed=42`), they will return the same values at each call.
    In order to get different values at each call, you must use a
    `SeedGenerator` instead as the seed argument. The `SeedGenerator`
    object is stateful.

    Example:

    ```python
    seed_gen = keras_core.random.SeedGenerator(seed=42)
    values = keras_core.random.normal(shape=(2, 3), seed=seed_gen)
    new_values = keras_core.random.normal(shape=(2, 3), seed=seed_gen)
    ```

    Usage in a layer:

    ```python
    class Dropout(keras_core.Layer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.seed_generator = keras_core.random.SeedGenerator(1337)

        def call(self, x, training=False):
            if training:
                return keras_core.random.dropout(
                    x, rate=0.5, seed=self.seed_generator
                )
            return x
    ```
    """

    def __init__(self, seed=None, **kwargs):
        custom_backend = kwargs.pop("backend", None)
        if kwargs:
            raise ValueError(f"Unrecognized keyword arguments: {kwargs}")
        if custom_backend is not None:
            self.backend = custom_backend
        else:
            self.backend = backend

        if seed is None:
            rng, seed = backend.random.make_default_seed()
        else:
            rng, seed = backend.random.make_initial_seed(seed)

        if backend.backend() == "tensorflow":
            seed_dtype = "int32"
        else:
            seed_dtype = "uint32"

        self._initial_seed = seed
        self._rng = rng
        self.state = self.backend.Variable(
            self.backend.convert_to_tensor(seed),
            shape=tuple(seed.shape),
            dtype=seed_dtype,
            trainable=False,
            name="seed_generator_state",
        )

    def next(self):
        if backend.backend() == "torch":
            seed_sub_state = self._rng.get_state()
            self.state.assign(seed_sub_state)
            return self._rng
        else:
            seed_state = self.backend.convert_to_tensor(self.state)
            seed_state, seed_sub_state = self.backend.random.get_next_state(
                seed_state
            )
            self.state.assign(seed_sub_state)
            return seed_sub_state


def global_seed_generator(seed):
    gen = global_state.get_global_attribute("global_seed_generator")
    if gen is None:
        gen = global_state.set_global_attribute("global_seed_generator", seed)
    return gen


def draw_seed(seed):
    if seed is None:
        gen = global_state.get_global_attribute("global_seed_generator")
        if gen is None:
            rng = SeedGenerator(seed)
            return global_seed_generator(rng)
        else:
            return gen.next()
    else:
        return SeedGenerator(seed).next()


@keras_core_export("keras_core.random.global_rng_state")
def global_rng_state():
    """Returns the state variable for the default global RNG.

    Returns:
        A `KerasVariable` with shape `(2,)` and dtype `uint32`.
    """

    gen = global_state.get_global_attribute("global_seed_generator")
    if gen:
        return gen.state()
    return None
