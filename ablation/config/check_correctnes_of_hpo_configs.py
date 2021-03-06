# -*- coding: utf-8 -*-

"""Validates the HPO configs."""

import json
import os
from typing import Dict, Iterable

HERE = os.path.abspath(os.path.dirname(__file__))

MODEL_DIRECTORIES_TO_MODEL_NAME = {
    'complex': 'ComplEx',
    'conve': 'ConvE',
    'convkb': 'ConvKB',
    'distmult': 'DistMult',
    'ermlp': 'ERMLP',
    'hole': 'HolE',
    'kg2e': 'KG2E',
    'ntn': 'NTN',
    'proje': 'ProjE',
    'rescal': 'RESCAL',
    'rgcn': 'RGCN',
    'rotate': 'RotatE',
    'simple': 'SimplE',
    'structured_embedding': 'StructuredEmbedding',
    'transd': 'TransD',
    'transe': 'TransE',
    'transh': 'TransH',
    'transr': 'TransR',
    'tucker': 'TuckER',
    'unstructured_model': 'UnstructuredModel',
}

MODEL_NAME_TO_DIRECTORIES = {val: key for key, val in MODEL_DIRECTORIES_TO_MODEL_NAME.items()}

DATASET_NAMES = ['fb15k237', 'kinships', 'wn18rr', 'yago310', 'examples']

NUM_LCWA_CONFIGS = 3
NUM_OWA_CONFIGS = 4

REDUCED = 'reduced'
REDUCED_EMBEDDING_SETTING = {
    "type": "int",
    "low": 6,
    "high": 8,
    "scale": "power_two",
}

REDUCED_SETTING = {
    'embedding_dim': REDUCED_EMBEDDING_SETTING,
}

SETTING = {
    REDUCED: REDUCED_SETTING,
}

DEFINED_REGULARIZERS = ['NoRegularizer']
NUM_REGULARIZERS = 1
REGULARIZER_KWARGS = {
    'NoRegularizer': {}
}
REGULARIZER_KWARGS_RANGES = {
    'NoRegularizer': {}
}


def iterate_config_paths(root_directory: str) -> Iterable[str]:
    """Iterate over all configuration paths."""
    root_directory = os.path.join(HERE, root_directory)
    for model in os.listdir(root_directory):
        # Check, whether model is valid
        if model.startswith('.'):
            continue

        assert model in MODEL_DIRECTORIES_TO_MODEL_NAME, f'Model {model} is unknown'
        model_directory = os.path.join(root_directory, model)

        # Check, whether required datasets are defined
        datasets = os.listdir(model_directory)

        assert len(datasets) == len(DATASET_NAMES) and [dataset in datasets for dataset in DATASET_NAMES], \
            f'It is excepted that configurations for \'examples\', \'fb15k237\', \'kinships\', \'wn18rr\' and' \
                f' \'yago310\' are prvovided, but got' \
                f' {datasets[0]}, {datasets[1]}, {datasets[2]}, {datasets[3]} and {datasets[4]}.'

        for dataset in datasets:
            if dataset not in DATASET_NAMES and dataset != 'examples':
                raise Exception(f"Dataset {dataset} is unknown.")

            if dataset == 'examples':
                continue

            # Check, whether correct HPO approach is defined
            hpo_approach_directory = os.path.join(root_directory, model_directory, dataset)
            hpo_approach = os.listdir(hpo_approach_directory)

            assert len(
                hpo_approach) == 1 and hpo_approach[0] == 'random', \
                "Currently, only random search is allowed as HPO approach."

            # Check, whether correct training assumptions are defined
            training_assumption_directory = os.path.join(
                root_directory,
                model_directory,
                dataset,
                hpo_approach[0],
            )
            training_assumptions = os.listdir(training_assumption_directory)
            assert len(training_assumptions) == 2 and 'lcwa' in training_assumptions and 'owa' in training_assumptions, \
                f'It is expected that only configurations for LCWA and OWA are provided, but got ' \
                    f'{training_assumptions[0]} and {training_assumptions[1]}'

            for training_assumption in training_assumptions:
                configs_directory = os.path.join(
                    root_directory,
                    model_directory,
                    dataset,
                    hpo_approach[0],
                    training_assumption,
                )
                configs = os.listdir(configs_directory)

                # Check, whether correct number of configurations are defined
                # if training_assumption == 'lcwa':
                #     assert len(
                #         configs) == NUM_LCWA_CONFIGS, f"More than one LCWA config provided ({configs_directory})."
                # else:
                #     assert training_assumption == 'owa' and len(
                #         configs) == NUM_OWA_CONFIGS, f'For owa exactly {NUM_OWA_CONFIGS} configurations' \
                #         f' are required, but {len(configs)} were provided'

                for config in configs:
                    yield model, dataset, hpo_approach, training_assumption, config, configs_directory


def filter_provided_setting(model_name: str, provided_setting: Dict, key_of_interest: str) -> Dict:
    """"""
    provided_setting = {model_name:
        {
            key: value for key, value in provided_setting.items() if key == key_of_interest
        }
    }

    return provided_setting


def create_expected_setting(model_name: str, key: str) -> Dict:
    """."""
    expected_setting = {model_name: {key: REDUCED_SETTING[key]}}

    return expected_setting


def check_adam_adadelta_configs(configuration, config_name, model_name_normalized):
    """."""
    optimizers = configuration['ablation']['optimizers']
    optimizer = optimizers[0]

    assert len(optimizers) == 1

    assert optimizer in config_name

    optimizer_kwargs = configuration['ablation']['optimizer_kwargs'][
        MODEL_DIRECTORIES_TO_MODEL_NAME[model_name_normalized]]
    assert len(optimizer_kwargs) == 1

    assert len(optimizer_kwargs[optimizer]) == 1
    assert optimizer_kwargs[optimizer]['weight_decay'] == 0.

    loss_fcts = configuration['ablation']['loss_functions']

    assert len(loss_fcts) == 2
    assert 'BCEAfterSigmoidLoss' in loss_fcts and 'SoftplusLoss' in loss_fcts


def check_mrl_configs(configuration, model_name_normalized):
    """."""

    optimizers = configuration['ablation']['optimizers']

    assert len(optimizers) == 2

    assert 'adadelta' in optimizers and 'adadelta' in optimizers

    optimizer_kwargs = configuration['ablation']['optimizer_kwargs'][
        MODEL_DIRECTORIES_TO_MODEL_NAME[model_name_normalized]]
    assert len(optimizer_kwargs) == 2

    loss_fcts = configuration['ablation']['loss_functions']
    loss_fct = loss_fcts[0]
    assert len(loss_fcts) == 1
    assert 'MarginRankingLoss' == loss_fct

    model = MODEL_DIRECTORIES_TO_MODEL_NAME[model_name_normalized]
    provided_margin = configuration['ablation']['loss_kwargs_ranges'][model]['MarginRankingLoss']['margin']
    margin = {
        "type": "float",
        "low": 0.5,
        "high": 10,
        "q": 1.0
    }

    assert provided_margin == margin


def check_nssal_configs(configuration, model_name_normalized):
    """."""

    optimizers = configuration['ablation']['optimizers']

    assert len(optimizers) == 2

    assert 'adadelta' in optimizers and 'adadelta' in optimizers

    optimizer_kwargs = configuration['ablation']['optimizer_kwargs'][
        MODEL_DIRECTORIES_TO_MODEL_NAME[model_name_normalized]]
    assert len(optimizer_kwargs) == 2

    loss_fcts = configuration['ablation']['loss_functions']
    loss_fct = loss_fcts[0]
    assert len(loss_fcts) == 1
    assert 'NSSALoss' == loss_fct

    model = MODEL_DIRECTORIES_TO_MODEL_NAME[model_name_normalized]
    provided_margin = configuration['ablation']['loss_kwargs_ranges'][model]['NegativeSamplingSelfAdversarialLoss'][
        'margin']
    margin = {
        "type": "float",
        "low": 1.,
        "high": 30,
        "q": 2.0
    }
    assert provided_margin == margin
    provided_temperature = \
        configuration['ablation']['loss_kwargs_ranges'][model]['NegativeSamplingSelfAdversarialLoss'][
            'adversarial_temperature']
    temperature = {
        "type": "float",
        "low": 0.1,
        "high": 1.0,
        "q": 0.1
    }

    assert provided_temperature == temperature


if __name__ == '__main__':
    iterator = iterate_config_paths(root_directory='reduced_search_space')

    for model_name_normalized, dataset, hpo_approach, training_assumption, config_name, path in iterator:
        with open(os.path.join(path, config_name), 'r') as file:
            try:
                configuration = json.load(file)
            except:
                raise Exception(f"{config_name} could not be loaded.")
            ablation_setting = configuration['ablation']
            model_name = MODEL_DIRECTORIES_TO_MODEL_NAME[model_name_normalized]

            # check embedding setting
            provided_setting = ablation_setting['model_kwargs'][model_name]
            assert 'embedding_dim' not in provided_setting, f'Embedding dimension provided' \
                f' in model_kwargs for {config_name}'

            provided_setting = ablation_setting['model_kwargs_ranges'][model_name]
            provided_setting = filter_provided_setting(
                model_name=model_name,
                provided_setting=provided_setting,
                key_of_interest='embedding_dim',
            )
            expected_setting = create_expected_setting(model_name=model_name, key='embedding_dim')
            assert expected_setting == provided_setting, f'Error in embedding setting' \
                f' for configuration {config_name}.'

            # check regularization setting
            provided_regularizers = ablation_setting['regularizers']
            provided_setting_kwargs = ablation_setting['regularizer_kwargs']
            provided_setting_kwargs_ranges = ablation_setting['regularizer_kwargs_ranges']
            if model_name == 'TransH':
                expected_regularizers = ['TransH']
                expected_setting_kwargs = {
                    "TransH": {
                        "TransH": {
                            "epsilon": 1e-5
                        }
                    }
                }
                expected_setting_kwargs_ranges = {
                    "TransH": {
                        "TransH": {
                            "weight": {
                                "type": "float",
                                "low": 0.01,
                                "high": 0.3,
                                "scale": "log"
                            }
                        }
                    }
                }
            else:
                expected_regularizers = ['NoRegularizer']
                expected_setting_kwargs = {
                    model_name: {
                        "NoRegularizer": {}
                    }
                }
                expected_setting_kwargs_ranges = expected_setting_kwargs

            assert expected_regularizers == provided_regularizers, f'Wrong regularizers defiend in {config_name}.'
            assert expected_setting_kwargs == provided_setting_kwargs, f'Regularizer arguments provided' \
                f' in regularizer_kwargs for {config_name}'

            assert expected_setting_kwargs_ranges == provided_setting_kwargs_ranges, f'Regularizer arguments provided' \
                f' in regularizer_kwargs_ranges for {config_name}'

            # Check correctness of negative sampling setting for OWA
            if training_assumption.lower() == 'owa':
                provided_setting_kwargs = ablation_setting['negative_sampler_kwargs']
                provided_setting_kwargs_ranges = ablation_setting['negative_sampler_kwargs_ranges']
                expected_setting_kwargs = {
                    model_name: {
                        "BasicNegativeSampler": {}
                    }
                }
                expected_setting_kwargs_ranges = {
                    model_name: {
                        "BasicNegativeSampler": {
                            "num_negs_per_pos": {
                                "type": "int",
                                "low": 1,
                                "high": 100,
                                "q": 1
                            }
                        }
                    }
                }

                assert expected_setting_kwargs == provided_setting_kwargs, f'Negative saompler arguments provided' \
                    f' in negative_sampler_kwargs for {config_name}.'

                assert expected_setting_kwargs_ranges == provided_setting_kwargs_ranges, f'Error in ' \
                    f' negative_sampler_kwargs_ranges for {config_name}.'

                # Check, whether correct model is defined
                defined_models = configuration['ablation']['models']
                assert len(
                    defined_models) == 1, f'Expected exactly one model, but provided {len(defined_models)} models.'
                defined_model = defined_models[0]
                assert MODEL_NAME_TO_DIRECTORIES[defined_model] in path

                # Check, whether correct dataset is defined
                defined_datasets = configuration['ablation']['datasets']
                assert len(
                    defined_datasets) == 1, f'Expected exactly one dataset, but provided {len(defined_datasets)} datasets.'
                defined_dataset = defined_datasets[0]
                assert defined_dataset in path, f'{defined_dataset} not in {os.path.join(path, config_name)}'
                assert defined_dataset in configuration['metadata']['title'].lower().replace('-', '').replace('_', ''), \
                    f'Wrong dataset defined in title in configuration {config_name}.'

                # Check correctness early stopping config
                expected_setting = 'early'
                assert configuration['ablation'][
                           'stopper'] == expected_setting, f'Stopper not defined correctly in{config_name}.'

                expected_setting = {
                    "frequency": 50,
                    "patience": 2,
                    "delta": 0.002
                }
                provided_setting = configuration['ablation']['stopper_kwargs']
                assert expected_setting == provided_setting, f'Stopper_kwargs not defined correctly in {config_name}.'

                # Check correctness of loss functions and optimizers
                if 'adadelta' in config_name or 'adadelta' in config_name:
                    check_adam_adadelta_configs(configuration, config_name, model_name_normalized)
                elif 'mrl' in config_name:
                    check_mrl_configs(configuration, model_name_normalized)
                elif 'nssal' in config_name:
                    check_nssal_configs(configuration, model_name_normalized)
