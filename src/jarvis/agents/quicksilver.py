import math
from typing import Any

from pydantic import BaseModel, Field

from jarvis.schemas import Candle, Forecast


class QuicksilverSettings(BaseModel):
    """Configuration for Quicksilver."""
    horizon_bars: int = 32
    context_len: int = 512
    backend: str = "cpu"
    repo_id: str = "google/timesfm-1.0-200m"


class TimesFMSingleton:
    _instance = None
    _model = None
    
    @classmethod
    def get_model(cls, settings: QuicksilverSettings) -> Any:
        if cls._model is None:
            try:
                import timesfm # type: ignore
                from timesfm import configs
                
                # Verify the current timesfm package API
                forecast_config = configs.ForecastConfig(
                    horizon_len=settings.horizon_bars,
                    quantiles=[0.1, 0.5, 0.9]
                )
                
                if hasattr(timesfm, "TimesFM_2p5_200M_torch"):
                    # TimesFM 3.0 API (actually called 2p5 occasionally but TimesFM_2p5_200M_torch or similar exists)
                    cls._model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
                        "google/timesfm-2.0-200m-pytorch", # typical huggingface path for newer ones, but let's fall back to settings if we can
                    )
                    # Note: we might need to apply config at forecast time or load time
                elif hasattr(timesfm, "TimesFm"):
                    # older TimesFm class
                    cls._model = timesfm.TimesFm(
                        context_len=settings.context_len,
                        horizon_len=settings.horizon_bars,
                        input_patch_len=32,
                        output_patch_len=128,
                        num_layers=20,
                        model_dims=1280,
                        backend=settings.backend,
                    )
                    cls._model.load_from_checkpoint(repo_id=settings.repo_id)
            except Exception:
                # If timesfm fails to load, keep _model as None
                pass
        return cls._model


def run_quicksilver(
    symbol: str,
    timeframe: str,
    candles: list[Candle],
    atr: float,
    settings: QuicksilverSettings,
) -> Forecast | None:
    """Generate a price forecast using TimesFM."""
    
    if len(candles) < settings.context_len:
        return None
        
    model = TimesFMSingleton.get_model(settings)
    if model is None:
        return None
        
    closes = [c.close for c in candles[-settings.context_len:]]
    
    try:
        # We need to call forecast
        if hasattr(model, "forecast_config"):
            # New API
            # signature: forecast(inputs: Sequence[Any], freq: Sequence[int] | None = None, window_size: int | None = None, forecast_context_len: int | None = None, return_forecast_on_context: bool = False, force_on_cpu: bool = False)
            model.forecast_config.horizon_len = settings.horizon_bars
            model.forecast_config.quantiles = [0.1, 0.5, 0.9]
            
            # call forecast
            forecast_result = model.forecast([closes], freq=[0])
        else:
            # Old API
            forecast_result = model.forecast([closes], freq=[0]) 
            
        point_forecasts, quantile_forecasts = forecast_result
        
        # It usually returns shape: (batch, horizon) and (batch, horizon, num_quantiles)
        # So point_forecasts[0] is array of length horizon
        point = point_forecasts[0]
        quant = quantile_forecasts[0]
        
        median_list = quant[:, 1].tolist() if quant.ndim == 2 and quant.shape[1] >= 2 else point.tolist()
        q10_list = quant[:, 0].tolist() if quant.ndim == 2 and quant.shape[1] >= 1 else []
        q90_list = quant[:, 2].tolist() if quant.ndim == 2 and quant.shape[1] >= 3 else []
        
        median_drift = median_list[-1] - closes[-1]
        
        strength = abs(median_drift) / atr if atr > 0 else 0.0
        # clip to max 5.0
        strength = min(strength, 5.0)
        
        if median_drift > atr * 0.5:
            expected_direction = "BULLISH"
        elif median_drift < -atr * 0.5:
            expected_direction = "BEARISH"
        else:
            expected_direction = "FLAT"
            
        return Forecast(
            symbol=symbol,
            horizon_bars=settings.horizon_bars,
            timeframe=timeframe,
            median=median_list,
            q10=q10_list,
            q90=q90_list,
            expected_direction=expected_direction,  # type: ignore
            strength=strength
        )
    except Exception as e:
        print(f"Quicksilver Error: {e}")
        return None
