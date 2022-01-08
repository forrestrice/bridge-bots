import tensorflow as tf
from tensorflow.python.lib.io.tf_record import TFRecordCompressionType


def decode_fn(record_bytes):
  return tf.io.parse_single_example(
      # Data
      record_bytes,

      # Schema
      {"x": tf.io.FixedLenFeature([], dtype=tf.float32),
       "y": tf.io.FixedLenFeature([], dtype=tf.float32)}
  )


filename = "/Users/frice/bridge/bid_learn/one_hand/toy/train.tfrecords.gz"
tf_record_dataset = tf.data.TFRecordDataset([filename], compression_type=TFRecordCompressionType.GZIP)
tf_record_dataset.tak
