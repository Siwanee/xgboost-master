'''Loading a pickled model generated by test_pickling.py, only used by
`test_gpu_with_dask.py`'''
import os
import numpy as np
import xgboost as xgb
import json
import pytest
import sys

from test_gpu_pickling import build_dataset, model_path, load_pickle

sys.path.append("tests/python")
import testing as tm


class TestLoadPickle:
    def test_load_pkl(self):
        '''Test whether prediction is correct.'''
        assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1'
        bst = load_pickle(model_path)
        x, y = build_dataset()
        test_x = xgb.DMatrix(x)
        res = bst.predict(test_x)
        assert len(res) == 10

    def test_predictor_type_is_auto(self):
        '''Under invalid CUDA_VISIBLE_DEVICES, predictor should be set to
        auto'''
        assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1'
        bst = load_pickle(model_path)
        config = bst.save_config()
        config = json.loads(config)
        assert config['learner']['gradient_booster']['gbtree_train_param'][
            'predictor'] == 'auto'

    def test_predictor_type_is_gpu(self):
        '''When CUDA_VISIBLE_DEVICES is not specified, keep using
        `gpu_predictor`'''
        assert 'CUDA_VISIBLE_DEVICES' not in os.environ.keys()
        bst = load_pickle(model_path)
        config = bst.save_config()
        config = json.loads(config)
        assert config['learner']['gradient_booster']['gbtree_train_param'][
            'predictor'] == 'gpu_predictor'

    def test_wrap_gpu_id(self):
        assert os.environ['CUDA_VISIBLE_DEVICES'] == '0'
        bst = load_pickle(model_path)
        config = bst.save_config()
        config = json.loads(config)
        assert config['learner']['generic_param']['gpu_id'] == '0'

        x, y = build_dataset()
        test_x = xgb.DMatrix(x)
        res = bst.predict(test_x)
        assert len(res) == 10

    def test_training_on_cpu_only_env(self):
        assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1'
        rng = np.random.RandomState(1994)
        X = rng.randn(10, 10)
        y = rng.randn(10)
        with tm.captured_output() as (out, err):
            # Test no thrust exception is thrown
            with pytest.raises(xgb.core.XGBoostError):
                xgb.train({'tree_method': 'gpu_hist'}, xgb.DMatrix(X, y))

            assert out.getvalue().find('No visible GPU is found') != -1
