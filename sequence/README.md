# Sequence Learning

This package contains TensorFlow and Keras code which prepares Bridgebots data for model training. It is largely experimental, so documentation and testing is lacking relative to other Bridgebots packages.

There are three main components of the package:
1. Feature/Label generation
2. TF Dataset creation
3. Utilities for training and evaluating sequence based models (currently LSTMs)
4. Utilities for performing inference on Bridgebots data using trained models

See my introductory [blog post](https://forrestrice.com/posts/Bridgebots-ML-Introduction/) for more context on the goals and outcomes of the project so far.

## Feature/Label Generation
This package currently focuses on predicting the next bid, and the holding of each player in terms of hand shape and High Card Points (HCP) given a sequence of bids so far. TensorFlow provides a data format called a [SequenceExample](https://www.tensorflow.org/api_docs/python/tf/train/SequenceExample) which allows us to capture a combination of time series and contextual features.

Examples of time series features for Bridge bidding are:
* The position of the player to act next (dealer, dealer+1, etc)
* The holding of that player (52 bit tensor - one bit per card)
* The bidding so far (one-hot encoded)

Examples of context features for Bridge bidding are:
* The vulnerability of each team

For the sake of efficiency, labels are also generated and included as "features". Note that these should only be used as targets for the model predictions, not as features, since they will not be available at prediction time.

Example labels:
* The next bid in the sequence
* The HCP of each player
* The suit shape of each player (4 integers per player)

[create_sequence_examples](./bridgebots_sequence/create_sequence_examples.py) parses Bridgebots Deal objects and uses features from [bidding_context_features](./bridgebots_sequence/bidding_context_features.py) and [bidding_sequence_features.py](./bridgebots_sequence/bidding_sequence_features.py) to build a `SequenceExample` for each deal.

## TensorFlow Dataset Creation
 [dataset_pipeline](./bridgebots_sequence/dataset_pipeline.py) loads these `SequenceExamples` and prepares a [tf.data.Dataset](https://www.tensorflow.org/api_docs/python/tf/data/Dataset) for the label we would like to predict. It heavily relies on [tf.data.AUTOTUNE](https://www.tensorflow.org/guide/data_performance) to optimize performance during training. 

## Sequence Model Training
[train_bidding_lstm](./bridgebots_sequence/train_bidding_lstm.py) uses Keras to create an LSTM model with specified parameters. The Dataset is fed in and the model is trained and evaluated. Loss functions are assigned based on the target supplied (`CategoricalCrossentropy` for predicting the next bid, `MeanSquaredError` for predicting shapes or HCP). Finally, the model is saved along with a json metadata file which contains information about the features used by the model and the output type.

## Inference
[inference](./bridgebots_sequence/inference.py) loads one of the saved models and runs inference on a Bridgebots deal. Each type of predictive model has its own [interpreter](./bridgebots_sequence/interpreter.py), which can convert the raw output from the TensorFlow model into something that is easily understood (e.g. a dict mapping a player direction to their predicted number of high card points like NORTH:12). 