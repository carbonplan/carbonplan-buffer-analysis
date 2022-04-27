import pytest

from carbonplan_buffer_analysis.prefect.flows.calculate_tanoak_basal_area import get_fraction_tanoak


@pytest.mark.parametrize(
    "project, expected_result",
    [
        (
            {
                "opr_id": "XYZ123",
                "acreage": 100,
                "assessment_areas": [
                    {
                        "code": 1,
                        "site_class": "low",
                        "acreage": 100,
                        "species": [{"code": 999, "fraction": 1}],
                    }
                ],
            },
            0,
        ),
        (
            {
                "opr_id": "XYZ321",
                "acreage": 100,
                "assessment_areas": [
                    {
                        "code": 1,
                        "site_class": "low",
                        "acreage": 100,
                        "species": [
                            {"code": 631, "fraction": 0.5},
                            {"code": 999, "fraction": 0.5},
                        ],
                    }
                ],
            },
            0.5,
        ),
        (
            {
                "opr_id": "XYZ007",
                "acreage": 100,
                "assessment_areas": [
                    {
                        "code": 1,
                        "site_class": "low",
                        "acreage": 50,
                        "species": [
                            {"code": 631, "fraction": 0.5},
                            {"code": 999, "fraction": 0.5},
                        ],
                    },
                    {
                        "code": 1,
                        "site_class": "high",
                        "acreage": 50,
                        "species": [
                            {"code": 631, "fraction": 0.5},
                            {"code": 999, "fraction": 0.5},
                        ],
                    },
                ],
            },
            0.5,
        ),
        (
            {
                "opr_id": "XYZ999",
                "acreage": 100,
                "assessment_areas": [],
            },
            0,
        ),
    ],
)
def test_get_tanaok_fraction(project, expected_result):
    assert get_fraction_tanoak(project) == expected_result
