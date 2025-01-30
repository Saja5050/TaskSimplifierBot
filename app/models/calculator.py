def calculate(expression):
    """
    Evaluates a mathematical expression and returns the result.
    """
    try:
        result = eval(expression)  # Make sure to sanitize input
        return result
    except Exception as e:
        return f"Error in calculation: {e}"
