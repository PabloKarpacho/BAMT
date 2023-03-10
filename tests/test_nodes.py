import unittest
import logging
import pandas as pd
import numpy as np

import bamt.nodes as nodes

logging.getLogger("nodes").setLevel(logging.CRITICAL)


class TestBaseNode(unittest.TestCase):

    def test_equality(self):
        test = nodes.BaseNode(name="node0")
        first = nodes.BaseNode(name="node1")

        test_clone = test

        # different name
        self.assertFalse(test == first)
        self.assertTrue(test == test_clone)

        # different type
        test_clone.type = "gaussian"
        test.type = "gaussian"

        first.type = "discrete"

        self.assertFalse(test == first)
        self.assertTrue(test == test_clone)

        # different disc_parents
        disc_parents = [f"node{i}" for i in range(2, 6)]
        test.disc_parents, test_clone.disc_parents = disc_parents, disc_parents
        first = disc_parents[:3]

        self.assertFalse(test == first)
        self.assertTrue(test == test_clone)

        # different cont_parents
        cont_parents = [f"node{i}" for i in range(6, 10)]
        test.disc_parents, test_clone.disc_parents = cont_parents, cont_parents
        first = cont_parents[:3]

        self.assertFalse(test == first)
        self.assertTrue(test == test_clone)

        # different children
        children = [f"node{i}" for i in range(5)]
        test.disc_parents, test_clone.disc_parents = children, children
        first = children[:3]

        self.assertFalse(test == first)
        self.assertTrue(test == test_clone)

    # ???
    def test_choose_serialization(self):
        pass


class TestDiscreteNode(unittest.TestCase):

    def setUp(self):
        self.node = nodes.DiscreteNode(name="test")
        self.data_dict = {
            "node0": np.random.normal(0, 4, 30),
            "node1": np.random.normal(0, .1, 30),
            "node2": np.random.normal(0, .3, 30),
            "test": np.random.choice(["cat1", "cat2", "cat3"], 30),
            "node4": np.random.choice(["cat4", "cat5", "cat6"], 30),
            "node5": np.random.choice(["cat7", "cat8", "cat9"], 30),
            "node6": np.random.choice(["cat7", "cat8", "cat9"], 30),
        }

        self.node.disc_parents = ["node4", "node5"]
        # self.node.cont_parents = ["node0", "node1"]
        self.node.children = ["node6"]

    def test_fit_parameters(self):
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))
        self.assertIsNotNone(params["vals"])
        self.assertNotEqual(params["vals"], [])

        for comb, probas in params["cprob"].items():
            self.assertAlmostEqual(sum(probas), 1, delta=1e-5)

    def test_choose(self):
        pvals = ["cat4", "cat7"]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))

        self.assertTrue([self.node.choose(params, pvals) in params["vals"]])

    def test_predict(self):
        pvals = ["cat4", "cat7"]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))

        self.assertTrue([self.node.predict(params, pvals) in params["vals"]])
        self.assertRaises(KeyError, self.node.predict, params, ["bad", "values"])


class TestGaussianNode(unittest.TestCase):

    def setUp(self):
        self.node = nodes.GaussianNode(name="test")
        self.data_dict = {
            "node0": np.random.normal(1, 4, 30),
            "node1": np.random.normal(2, .1, 30),
            "foster-son": np.random.normal(2.5, .2, 30),
            "test": np.random.normal(3, .3, 30),
            "node2": np.random.choice(["cat1", "cat2", "cat3"], 30),
            "node4": np.random.choice(["cat4", "cat5", "cat6"], 30),
            "node5": np.random.choice(["cat7", "cat8", "cat9"], 30),
            "node6": np.random.choice(["cat7", "cat8", "cat9"], 30),
        }

        # self.node.disc_parents = ["node4", "node5"]
        self.node.cont_parents = ["node0", "node1"]
        self.node.children = ["node6"]

    def test_fit_parameters(self):
        node_without_parents = nodes.GaussianNode(name="foster-son")
        node_without_parents.children = ["node6", "node5"]

        params_parents = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))
        params_foster = node_without_parents.fit_parameters(pd.DataFrame.from_records(self.data_dict))

        self.assertIsNotNone(params_parents["regressor_obj"])
        self.assertTrue(pd.isna(params_parents["mean"]))
        self.assertIsNotNone(params_parents["variance"])

        self.assertIsNone(params_foster["regressor_obj"])
        self.assertFalse(pd.isna(params_foster["mean"]))
        self.assertIsNotNone(params_foster["variance"])

    def test_choose(self):
        pvals = [1.05, 1.95]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))

        self.assertTrue(isinstance(self.node.choose(params, pvals), float))

    def test_predict(self):
        pvals = [1.05, 1.95]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))
        self.assertTrue(isinstance(self.node.predict(params, pvals), float))
        self.assertRaises(ValueError, self.node.predict, params, ["bad", "values"])


class TestConditionalGaussianNode(unittest.TestCase):

    def setUp(self):
        self.node = nodes.ConditionalGaussianNode(name="test")
        self.data_dict = {
            "node0": np.random.normal(1, 4, 30),
            "node1": np.random.normal(2, .1, 30),
            "foster-son": np.random.normal(2.5, .2, 30),
            "test": np.random.normal(3, .3, 30),
            "node2": np.random.choice(["cat1", "cat2", "cat3"], 30),
            "node4": np.random.choice(["cat4", "cat5", "cat6"], 30),
            "node5": np.random.choice(["cat7", "cat8", "cat9"], 30),
            "node6": np.random.choice(["cat7", "cat8", "cat9"], 30),
        }

        self.node.disc_parents = ["node4", "node5"]
        self.node.cont_parents = ["node0", "node1"]
        self.node.children = ["node6"]

    def test_fit_parameters(self):
        node_without_parents = nodes.ConditionalGaussianNode(name="foster-son")
        node_without_parents.children = ["node6", "node5"]

        params_parents = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))["hybcprob"]
        params_foster = node_without_parents.fit_parameters(pd.DataFrame.from_records(self.data_dict))["hybcprob"]['[]']

        self.assertIsNone(params_foster["regressor_obj"])
        self.assertIsNotNone(params_foster["mean"])

        # Since there can be empty dictionaries,
        # we have to count them and if a percent is greater than the threshold test failed.
        report = []
        for comb, data in params_parents.items():
            if all(pd.isna(x) for x in data.values()):
                report.append(1)
                continue
            else:
                report.append(0)

            if pd.isna(data["mean"]):
                self.assertIsNotNone(data["regressor_obj"])
                self.assertIsNotNone(data["variance"])
            else:
                self.assertIsNone(data["regressor_obj"])
                self.assertIsNotNone(data["mean"])

        self.assertLess(sum(report)/len(report), 0.3)

    def test_choose(self):
        pvals = [1.05, 1.95, "cat4", "cat7"]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))
        self.assertTrue(isinstance(self.node.choose(params, pvals), float))

    def test_predict(self):
        pvals = [1.05, 1.95, "cat4", "cat7"]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))

        self.assertTrue(isinstance(self.node.predict(params, pvals), float))
        self.assertRaises(KeyError, self.node.predict, params, ["bad", "values"])


class TestMixtureGaussianNode(unittest.TestCase):

    def setUp(self):
        self.node = nodes.MixtureGaussianNode(name="test")
        self.data_dict = {
            "node0": np.random.normal(1, 4, 30),
            "node1": np.random.normal(2, .1, 30),
            "test": np.random.normal(3, .3, 30),
            "node2": np.random.choice(["cat1", "cat2", "cat3"], 30),
            "node4": np.random.choice(["cat4", "cat5", "cat6"], 30),
            "node5": np.random.choice(["cat7", "cat8", "cat9"], 30),
            "node6": np.random.choice(["cat7", "cat8", "cat9"], 30),
        }

        # self.node.disc_parents = ["node4", "node5"]
        self.node.cont_parents = ["node0", "node1"]
        self.node.children = ["node6"]

    def test_fit_parameters(self):
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))
        self.assertAlmostEqual(sum(params["coef"]), 1, delta=1e-5)

    def test_choose(self):
        pvals = [1.05, 1.95]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))
        self.assertTrue(isinstance(self.node.choose(params, pvals), float))

    def test_predict(self):
        pvals = [1.05, 1.95]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))

        self.assertTrue(isinstance(self.node.predict(params, pvals), float))


class TestConditionalMixtureGaussianNode(unittest.TestCase):

    def setUp(self):
        self.node = nodes.ConditionalMixtureGaussianNode(name="test")
        self.data_dict = {
            "node0": np.random.normal(1, 4, 30),
            "node1": np.random.normal(2, .1, 30),
            "test": np.random.normal(3, .3, 30),
            "node2": np.random.choice(["cat1", "cat2", "cat3"], 30),
            "node4": np.random.choice(["cat4", "cat5", "cat6"], 30),
            "node5": np.random.choice(["cat7", "cat8", "cat9"], 30),
            "node6": np.random.choice(["cat7", "cat8", "cat9"], 30),
        }

        self.node.disc_parents = ["node4", "node5"]
        self.node.cont_parents = ["node0", "node1"]
        self.node.children = ["node6"]

    def test_fit_parameters(self):
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))["hybcprob"]
        report = []
        # sometimes combination's data can be empty, so we set the percent of empty combinations
        for comb, data in params.items():
            if np.isclose(sum(data["coef"]), 1, atol=1e-5):
                report.append(0)
            else:
                report.append(1)
        self.assertLess(sum(report)/len(report), 0.3)

    def test_choose(self):
        pvals = [1.05, 1.95, "cat4", "cat7"]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))
        self.assertTrue(isinstance(self.node.choose(params, pvals), float))

    def test_predict(self):
        pvals = [1.05, 1.95, "cat4", "cat7"]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))

        self.assertTrue(isinstance(self.node.predict(params, pvals), float))


class TestLogitNode(unittest.TestCase):

    def setUp(self):
        self.node = nodes.LogitNode(name="test")
        self.data_dict = {
            "node0": np.random.normal(1, 4, 30),
            "node1": np.random.normal(2, .1, 30),
            "node2": np.random.normal(3, .3, 30),
            "test": np.random.choice(["cat1", "cat2", "cat3"], 30),
            "node4": np.random.choice(["cat4", "cat5", "cat6"], 30),
            "node5": np.random.choice(["cat7", "cat8", "cat9"], 30),
            "node6": np.random.choice(["cat7", "cat8", "cat9"], 30),
        }

        # self.node.disc_parents = ["node4", "node5"]
        self.node.cont_parents = ["node0", "node1"]
        self.node.children = ["node6"]

    def test_fit_parameters(self):
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))
        self.assertIsNotNone(params["classifier_obj"])

    def test_choose(self):
        pvals = [1.05, 1.95]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))
        self.assertTrue(self.node.choose(params, pvals) in params["classes"])

    def test_predict(self):
        pvals = [1.05, 1.95]
        params = self.node.fit_parameters(pd.DataFrame.from_records(self.data_dict))

        self.assertTrue([self.node.predict(params, pvals) in params["classes"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
