import json

import botocore.session
from botocore.stub import Stubber
import pytest

import lambda_function

AGENT_SERVICE_ARN = 'arn:aws:ecs:us-east-1:123456789012:service/AgentService'
CLUSTER_ARN = 'arn:aws:ecs:us-east-1:123456789012:cluster/cluster1'


def load_json_from_file(json_path):
    with open(json_path) as f:
        return json.load(f)


@pytest.fixture
def ecs_event():
    return load_json_from_file('fixtures/sample_ecs_event.json')


@pytest.fixture
def ecs_task_event():
    return load_json_from_file('fixtures/sample_ecs_task_event.json')


@pytest.fixture
def ec2_event():
    return load_json_from_file('fixtures/sample_ec2_event.json')


@pytest.fixture
def cluster_response():
    return load_json_from_file('fixtures/sample_describe_cluster_response.json')


def test_no_event_raises():
    with pytest.raises(ValueError):
        lambda_function.lambda_handler(None, None)


def test_event_non_ecs(ec2_event):
    with pytest.raises(ValueError):
        lambda_function.lambda_handler(ec2_event, None)


def test_no_service_env_var(ecs_event):
    with pytest.raises(ValueError):
        lambda_function.lambda_handler(ecs_event, None)


def test_event_no_match(ecs_task_event, capsys, monkeypatch):
    monkeypatch.setenv('ECS_SERVICE_ARN', AGENT_SERVICE_ARN)
    lambda_function.lambda_handler(ecs_task_event, None)
    out, _err = capsys.readouterr()
    assert out.strip() == "SKIP: Function operates only on ECS Container Instance State Change events."


def test_event_matches(ecs_event, mocker, monkeypatch):
    monkeypatch.setenv('ECS_SERVICE_ARN', AGENT_SERVICE_ARN)
    # Don't actually run the underlying function, only ensure it was called
    mocker.patch.object(lambda_function, 'adjust_service_desired_count')
    lambda_function.lambda_handler(ecs_event, None)
    assert lambda_function.adjust_service_desired_count.call_count == 1


def tests_skip_when_service_not_in_cluster(capsys):
    ecs = botocore.session.get_session().create_client('ecs')
    stubber = Stubber(ecs)

    describe_services_response = {
        'services': []
    }
    expected_params = {'cluster': 'cluster1', 'services': [AGENT_SERVICE_ARN]}
    stubber.add_response('describe_services', describe_services_response, expected_params)

    with stubber:
        response = lambda_function.adjust_service_desired_count(ecs, 'cluster1', AGENT_SERVICE_ARN)
        out, _err = capsys.readouterr()
    assert response is None
    assert out.strip() == "SKIP: Service not found in cluster cluster1"


def test_adjusts_service_when_mismatch(cluster_response):
    ecs = botocore.session.get_session().create_client('ecs')
    stubber = Stubber(ecs)

    describe_services_response = {
        'services': [
            {
                'serviceArn': AGENT_SERVICE_ARN,
                'serviceName': 'AgentService',
                'clusterArn': CLUSTER_ARN,
                'desiredCount': 2,
            }
        ]
    }
    expected_params = {'cluster': 'cluster1', 'services': [AGENT_SERVICE_ARN]}
    stubber.add_response('describe_services', describe_services_response, expected_params)

    expected_params = {'clusters': ['cluster1']}
    stubber.add_response('describe_clusters', cluster_response, expected_params)

    update_service_response = {
        'service': {
            'serviceArn': AGENT_SERVICE_ARN,
            'serviceName': 'AgentService',
            'clusterArn': CLUSTER_ARN,
            'desiredCount': 3,
        }
    }
    expected_params = {'cluster': 'cluster1', 'desiredCount': 3, 'service': AGENT_SERVICE_ARN}
    stubber.add_response('update_service', update_service_response, expected_params)

    with stubber:
        response = lambda_function.adjust_service_desired_count(ecs, 'cluster1', AGENT_SERVICE_ARN)
        assert response == update_service_response


def test_adjusts_nothing_when_equal(cluster_response):
    ecs = botocore.session.get_session().create_client('ecs')
    stubber = Stubber(ecs)

    describe_services_response = {
        'services': [
            {
                'serviceArn': AGENT_SERVICE_ARN,
                'serviceName': 'AgentService',
                'clusterArn': CLUSTER_ARN,
                'desiredCount': 3,
            }
        ]
    }
    expected_params = {'cluster': 'cluster1', 'services': [AGENT_SERVICE_ARN]}
    stubber.add_response('describe_services', describe_services_response, expected_params)

    expected_params = {'clusters': ['cluster1']}
    stubber.add_response('describe_clusters', cluster_response, expected_params)

    with stubber:
        response = lambda_function.adjust_service_desired_count(ecs, 'cluster1', AGENT_SERVICE_ARN)
        assert response is None
