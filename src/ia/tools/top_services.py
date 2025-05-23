def get_top_services(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Obtém os serviços mais custosos da conta AWS.
    
    Returns:
        Lista de serviços mais custosos
    """
    cost_explorer = CostExplorer()
    return cost_explorer.get_top_services(start_date, end_date)