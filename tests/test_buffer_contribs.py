from carbonplan_buffer_analysis.prefect.flows import calculate_buffer_contributions


def test_all_projects():
    """Ensure all entries in issuance table have a fire risk number."""
    issuance = calculate_buffer_contributions.get_issuance_table.run()
    forest_projects = issuance.loc[issuance["project_type"] == "forest", "opr_id"].unique().tolist()
    fire_risks = calculate_buffer_contributions.load_project_fire_risks.run()
    for forest_project in forest_projects:
        assert forest_project in fire_risks
