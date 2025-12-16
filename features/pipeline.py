from .factory import FeatureFactory

def create_standard_pipeline() -> FeatureFactory:
    """
    Create a FeatureFactory with standard GARAM features registered.
    """
    factory = FeatureFactory()
    
    # Import library functions here to avoid circular imports
    # from .library import trend, volatility, sentiment, flow
    
    # factory.register_feature('trend_ma', trend.calc_ma_trend)
    # factory.register_feature('vol_atr', volatility.calc_atr)
    
    return factory
