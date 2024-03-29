import math
import numpy as np
import h5py
import matplotlib.pyplot as plt
import scipy
from PIL import Image
from scipy import ndimage
import tensorflow as tf
from tensorflow.python.framework import ops
from cnn_utils import *
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Just disables the warning, doesn't enable AVX/FMA

np.random.seed(1)

"""
---------------------------------------
 TENSORFLOW CNN TOWARDS AN APPLICATION
---------------------------------------
IN THIS PROGRAM YOU WILL:

1. Implement helper functions that you will use when implementing a TensorFlow model
2. Implement a fully functioning ConvNet using TensorFlow

After this you will be able to:

Build and train a ConvNet in TensorFlow for a classification problem

In the previous program, you built helper functions using numpy to understand the mechanics behind CNNs
Most practical applications of deep learning today are built using programming frameworks
Frameworks have many built-in functions you can simply call allowing for simpler usage

As usual, we will start by loading in the packages... done above

"""

# Load the signs dataset
# As a reminder, the SIGNS dataset is a collection of 6 signs representing numbers from 0 to 5
X_train_orig, Y_train_orig, X_test_orig, Y_test_orig, classes = load_dataset()
# Example of a picture
index = 6
plt.imshow(X_train_orig[index])
plt.show()
print("y value for shown image = " + str(np.squeeze(Y_train_orig[:, index])))

# In the past we built an FC NN for this dataset but since this is a dataset of images it is more natural to apply CNNs

# Let's start by examining the shapes of the given data

X_train = X_train_orig / 255.  # Convert 0-255 range of pixel values to 0-1 range
X_test = X_test_orig / 255.  # Convert 0-255 range of pixel values to 0-1 range
Y_train = convert_to_one_hot(Y_train_orig, 6).T  # Convert 0-5 value to a 5x1 matrix binary representation
Y_test = convert_to_one_hot(Y_test_orig, 6).T  # Convert 0-5 value to a 5x1 matrix binary representation

print("\n\nnumber of training examples = " + str(X_train.shape[0]))
print("number of test examples = " + str(X_test.shape[0]))

print("\nX_train shape: " + str(X_train.shape))
print("Y_train shape: " + str(Y_train.shape))

print("\nX_test shape: " + str(X_test.shape))
print("Y_test shape: " + str(Y_test.shape))

conv_layers = {}

'''
CREATE PLACEHOLDERS

TF requires that you create placeholders for the input data that will be fed into the model when running the session

Exercise: Implement the function below to create placeholders for the input image X and the output Y

You should not define the number of training examples for the moment
----> To do so, you could use "None" as the batch size, it will give you the flexibility to choose it later
----> Hence X should be of dimension [None, n_H0, n_W0, n_C0] and Y should be of dimension [None, n_y]

'''


# GRADED FUNCTION: create_placeholders

def create_placeholders(n_H0, n_W0, n_C0, n_y):
    """
    Creates the placeholders for the tensorflow session.

    Arguments:
    n_H0 -- scalar, height of an input image
    n_W0 -- scalar, width of an input image
    n_C0 -- scalar, number of channels of the input
    n_y -- scalar, number of classes

    Returns:
    X -- placeholder for the data input, of shape [None, n_H0, n_W0, n_C0] and dtype "float"
    Y -- placeholder for the input labels, of shape [None, n_y] and dtype "float"
    """

    X = tf.placeholder(dtype="float", shape=[None, n_H0, n_W0, n_C0], name="DATA_VALUES")
    Y = tf.placeholder(dtype="float", shape=[None, n_y], name="DATA_LABELS")

    return X, Y


print("\n\n-----CREATE PLACEHOLDERS-----")
X, Y = create_placeholders(64, 64, 3, 6)
print("\nX = " + str(X))
print("Y = " + str(Y))

'''
You will initialize weights/filters  W1  and  W2  using tf.contrib.layers.xavier_initializer(seed = 0)
You don't need to worry about bias variables as you will soon see that TensorFlow functions take care of the bias
Note: You will only initialize the weights/filters for the conv2d functions
--------> TensorFlow initializes the layers for the fully connected part automatically

Exercise: Implement initialize_parameters()

The dimensions for each group of filters are provided below
Reminder - to initialize a parameter  W  of shape [1,2,3,4] in Tensorflow, use:

W = tf.get_variable("W", [1,2,3,4], initializer = ...)

'''


# GRADED FUNCTION: initialize_parameters

def initialize_parameters():
    """
    Initializes weight parameters to build a neural network with tensorflow. The shapes are:
                        W1 : [4, 4, 3, 8]
                        W2 : [2, 2, 8, 16]
    Returns:
    parameters -- a dictionary of tensors containing W1, W2
    """

    tf.set_random_seed(1)  # so that your "random" numbers match ours

    W1 = tf.get_variable("W1", [4, 4, 3, 8], initializer=tf.contrib.layers.xavier_initializer(seed=0))
    W2 = tf.get_variable("W2", [2, 2, 8, 16], initializer=tf.contrib.layers.xavier_initializer(seed=0))

    parameters = {"W1": W1,
                  "W2": W2}

    return parameters


tf.reset_default_graph()

with tf.Session() as sess_test:
    parameters = initialize_parameters()
    init = tf.global_variables_initializer()
    sess_test.run(init)

    print("\n\n-----PARAMETER INITIALIZATION-----")
    print("\nW1 =\n"
          + str(parameters["W1"].eval()[1, 1, 1]))
    print("\nW2 =\n"
          + str(parameters["W2"].eval()[1, 1, 1]))

'''

*********************
 FORWARD PROPAGATION
*********************

In TensorFlow, there are built-in functions that carry out the convolution steps for you:

tf.nn.conv2d(X,W1, strides = [1,s,s,1], padding = 'SAME'): given an input  X  and a group of filters  W1
--> This function convolves  W1's filters on X
--> The third input ([1,f,f,1]) represents the strides for each dimension of the input (m, n_H_prev, n_W_prev, n_C_prev)
--> You can read the full documentation online

tf.nn.max_pool(A, ksize = [1,f,f,1], strides = [1,s,s,1], padding = 'SAME'): given an input A
--> This function uses a window of size (f, f) and strides of size (s, s) to carry out max pooling over each window
--> You can read the full documentation online

tf.nn.relu(Z1): 
--> Computes the element-wise ReLU of Z1 (which can be any shape)
--> You can read the full documentation online

tf.contrib.layers.flatten(P): given an input P
--> This function flattens each example into a 1D vector it while maintaining the batch-size
--> It returns a flattened tensor with shape [batch_size, k]
--> You can read the full documentation online

tf.contrib.layers.fully_connected(F, num_outputs): given a the flattened input F
--> This returns the output computed using a fully connected layer
--> You can read the full documentation online
--> The FC layer automatically initializes weights in the graph and keeps training them as you train the model
-----> Hence, you did not need to initialize those weights when initializing the parameters

Exercise:

Implement the forward_propagation function below to build the following model: 
CONV2D -> RELU -> MAXPOOL -> CONV2D -> RELU -> MAXPOOL -> FLATTEN -> FULLYCONNECTED

You should use the functions above.

------------------------------------------------------------------------------------------
        In detail, we will use the following parameters for all the steps:
------------------------------------------------------------------------------------------

 -- Conv2D: stride 1, padding is "SAME"
 -- ReLU
 -- Max pool: Use an 8 by 8 filter size and an 8 by 8 stride, padding is "SAME"

 -- Conv2D: stride 1, padding is "SAME"
 -- ReLU
 -- Max pool: Use a 4 by 4 filter size and a 4 by 4 stride, padding is "SAME"

 -- Flatten the previous output

 -- FULLYCONNECTED (FC) layer: Apply a fully connected layer without an non-linear activation function
 ----> Do not call the softmax here as the result is 6 neurons in the output layer, which later get passed to a softmax
 ----> In TF, the softmax and cost fn are lumped together into a single fn
 ----> You will call this lumped together fn in a different fn when computing the cost 

------------------------------------------------------------------------------------------

'''


# GRADED FUNCTION: forward_propagation

def forward_propagation(X, parameters):
    """
    Implements the forward propagation for the model:
    CONV2D -> RELU -> MAXPOOL -> CONV2D -> RELU -> MAXPOOL -> FLATTEN -> FULLYCONNECTED

    Arguments:
    X -- input dataset placeholder, of shape (input size, number of examples)
    parameters -- python dictionary containing your parameters "W1", "W2"
                  the shapes are given in initialize_parameters

    Returns:
    Z3 -- the output of the last LINEAR unit
    """

    # Retrieve the parameters from the dictionary "parameters" 
    W1 = parameters['W1']
    W2 = parameters['W2']

    # CONV2D: stride of 1, padding 'SAME'
    Z1 = tf.nn.conv2d(X, W1, strides=[1, 1, 1, 1], padding='SAME')

    # RELU
    A1 = tf.nn.relu(Z1)

    # MAXPOOL: window 8x8, sride 8, padding 'SAME'
    P1 = tf.nn.max_pool(A1, ksize=[1, 8, 8, 1], strides=[1, 8, 8, 1], padding='SAME')

    # CONV2D: filters W2, stride 1, padding 'SAME'
    Z2 = tf.nn.conv2d(P1, W2, strides=[1, 1, 1, 1], padding='SAME')

    # RELU
    A2 = tf.nn.relu(Z2)

    # MAXPOOL: window 4x4, stride 4, padding 'SAME'
    P2 = tf.nn.max_pool(A2, ksize=[1, 4, 4, 1], strides=[1, 4, 4, 1], padding='SAME')

    # FLATTEN
    P2 = tf.contrib.layers.flatten(P2)

    # FULLY-CONNECTED without non-linear activation function (not not call softmax).
    # 6 neurons in output layer. Hint: one of the arguments should be "activation_fn=None" 
    Z3 = tf.contrib.layers.fully_connected(P2, 6, activation_fn=None)

    return Z3


tf.reset_default_graph()

with tf.Session() as sess:
    np.random.seed(1)
    X, Y = create_placeholders(64, 64, 3, 6)
    parameters = initialize_parameters()
    Z3 = forward_propagation(X, parameters)
    init = tf.global_variables_initializer()
    sess.run(init)
    a = sess.run(Z3, {X: np.random.randn(2, 64, 64, 3), Y: np.random.randn(2, 6)})
    print("\n\n---FORWARD PROPOGATION TEST---")

    print("\nZ3 =\n"
          + str(a))

'''
COMPUTE COST

Implement the compute cost function below. You might find these two functions helpful:

tf.nn.softmax_cross_entropy_with_logits(logits = Z3, labels = Y): computes the softmax entropy loss
--> This function both computes the softmax activation function as well as the resulting loss
--> You can check the full documentation online

tf.reduce_mean: computes the mean of elements across dimensions of a tensor
--> Use this to sum the losses over all the examples to get the overall cost
--> You can check the full documentation online

Exercise: Compute the cost below using the function above

'''


def compute_cost(Z3, Y):
    """
    Computes the cost

    Arguments:
    Z3 -- output of forward propagation (output of the last LINEAR unit), of shape (6, number of examples)
    Y -- "true" labels vector placeholder, same shape as Z3

    Returns:
    cost - Tensor of the cost function
    """

    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=Z3, labels=Y))

    return cost


tf.reset_default_graph()

with tf.Session() as sess:
    np.random.seed(1)
    X, Y = create_placeholders(64, 64, 3, 6)
    parameters = initialize_parameters()
    Z3 = forward_propagation(X, parameters)
    cost = compute_cost(Z3, Y)
    init = tf.global_variables_initializer()
    sess.run(init)
    a = sess.run(cost, {X: np.random.randn(4, 64, 64, 3), Y: np.random.randn(4, 6)})

    print("\n\n---COMPUTE COST TEST---")
    print("\ncost =\n" + str(a))

'''
CREATING A MODEL

Finally you will merge the helper functions you implemented above to build a model
You will train it on the SIGNS dataset

You have implemented random_mini_batches() in the Optimization programming assignment of course 2
Remember that this function returns a list of mini-batches

Exercise: Complete the function below.

The model below should:

1. create placeholders
2. initialize parameters
3. forward propagate
4. compute the cost
5. create an optimizer

Finally you will create a session and run a for loop for num_epochs:
--> get the mini-batches
--> then for each mini-batch you will optimize the function

'''


# GRADED FUNCTION: model

def model(X_train, Y_train, X_test, Y_test, learning_rate=0.009,
          num_epochs=100, minibatch_size=64, print_cost=True):
    """
    Implements a three-layer ConvNet in Tensorflow:
    CONV2D -> RELU -> MAXPOOL -> CONV2D -> RELU -> MAXPOOL -> FLATTEN -> FULLYCONNECTED

    Arguments:
    X_train -- training set, of shape (None, 64, 64, 3)
    Y_train -- test set, of shape (None, n_y = 6)
    X_test -- training set, of shape (None, 64, 64, 3)
    Y_test -- test set, of shape (None, n_y = 6)
    learning_rate -- learning rate of the optimization
    num_epochs -- number of epochs of the optimization loop
    minibatch_size -- size of a minibatch
    print_cost -- True to print the cost every 100 epochs

    Returns:
    train_accuracy -- real number, accuracy on the train set (X_train)
    test_accuracy -- real number, testing accuracy on the test set (X_test)
    parameters -- parameters learnt by the model. They can then be used to predict.
    """

    ops.reset_default_graph()  # to be able to rerun the model without overwriting tf variables
    tf.set_random_seed(1)  # to keep results consistent (tensorflow seed)
    seed = 3  # to keep results consistent (numpy seed)
    (m, n_H0, n_W0, n_C0) = X_train.shape
    n_y = Y_train.shape[1]
    costs = []  # To keep track of the cost

    # Create Placeholders of the correct shape
    X, Y = create_placeholders(n_H0, n_W0, n_C0, n_y)

    # Initialize parameters
    parameters = initialize_parameters()

    # Forward propagation: Build the forward propagation in the tensorflow graph
    Z3 = forward_propagation(X, parameters)

    # Cost function: Add cost function to tensorflow graph
    cost = compute_cost(Z3, Y)

    # Backpropagation: Define the tensorflow optimizer. Use an AdamOptimizer that minimizes the cost.
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

    # Initialize all the variables globally
    init = tf.global_variables_initializer()

    # Start the session to compute the tensorflow graph
    with tf.Session() as sess:

        # Run the initialization
        sess.run(init)

        # Do the training loop
        for epoch in range(num_epochs):

            minibatch_cost = 0.
            num_minibatches = int(m / minibatch_size)  # number of minibatches of size minibatch_size in the train set
            seed = seed + 1
            minibatches = random_mini_batches(X_train, Y_train, minibatch_size, seed)

            for minibatch in minibatches:
                # Select a minibatch
                (minibatch_X, minibatch_Y) = minibatch
                # IMPORTANT: The line that runs the graph on a minibatch.
                # Run the session to execute the optimizer & the cost, the feeddict should contain a minibatch for (X,Y)

                _, temp_cost = sess.run([optimizer, cost], feed_dict={X: minibatch_X, Y: minibatch_Y})

                minibatch_cost += temp_cost / num_minibatches

            # Print the cost every epoch
            if print_cost and epoch % 5 == 0:
                print("Cost after epoch %i: %f" % (epoch, minibatch_cost))
            if print_cost and epoch % 1 == 0:
                costs.append(minibatch_cost)

        # plot the cost
        plt.plot(np.squeeze(costs))
        plt.ylabel('cost')
        plt.xlabel('iterations (per tens)')
        plt.title("Learning rate =" + str(learning_rate))
        plt.show()

        # Calculate the correct predictions
        predict_op = tf.argmax(Z3, 1)
        correct_prediction = tf.equal(predict_op, tf.argmax(Y, 1))

        # Calculate accuracy on the test set
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
        print(accuracy)
        train_accuracy = accuracy.eval({X: X_train, Y: Y_train})
        test_accuracy = accuracy.eval({X: X_test, Y: Y_test})
        print("Train Accuracy:", train_accuracy)
        print("Test Accuracy:", test_accuracy)

        return train_accuracy, test_accuracy, parameters


_, _, parameters = model(X_train, Y_train, X_test, Y_test)
