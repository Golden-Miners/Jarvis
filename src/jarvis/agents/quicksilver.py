"""Quicksilver agent — TimesFM price forecasting."""

from typing import Any

from pydantic import BaseModel

from jarvis.schemas import Candle, Forecast


class QuicksilverSettings(BaseModel):
    """Configuration for Quicksilver."""

    horizon_bars: int = 32
    context_len: int = 512
    backend: str = "cpu"
    repo_id: str = "google/timesfm-1.0-200m"


class TimesFMSingleton:
    """Lazy-loading singleton for the TimesFM model."""

    _instance = None
    _model = None

    @classmethod
    def get_model(cls, settings: QuicksilverSettings) -> Any:
        """Load or return cached TimesFM model."""
        if cls._model is not None:
            return cls._model
        try:
            import timesfm  # type: ignore
            from timesfm import configs

            configs.ForecastConfig(
                horizon_len=settings.horizon_bars,
                quantiles=[0.1, 0.5, 0.9],
            )

            if hasattr(timesfm, "TimesFM_2p5_200M_torch"):
                # TimesFM 3.x API
                repo = "google/timesfm-2.0-200m-pytorch"
                cls._model = (
                    timesfm.TimesFM_2p5_200M_torch
                    .from_pretrained(repo)
                )
            elif hasattr(timesfm, "TimesFm"):
                # Legacy 1.x API
                cls._model = timesfm.TimesFm(
                    context_len=settings.context_len,
                    horizon_len=settings.horizon_bars,
                    input_patch_len=32,
                    output_patch_len=128,
                    num_layers=20,
                    model_dims=1280,
                    backend=settings.backend,
                )
                cls._model.load_from_checkpoint(
                    repo_id=settings.repo_id,
                )
        except Exception:
            pass
        return cls._model

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (useful for testing)."""
        cls._model = None


def _extract_quantiles(
    point: Any,
    quant: Any,
) -> tuple[list[float], list[float], list[float]]:
    """Extract median, q10, q90 from forecast arrays."""
    if quant.ndim == 2 and quant.shape[1] >= 2:
        median = quant[:, 1].tolist()
    else:
        median = point.tolist()

    if quant.ndim == 2 and quant.shape[1] >= 1:
        q10 = quant[:, 0].tolist()
    else:
        q10 = []

    if quant.ndim == 2 and quant.shape[1] >= 3:
        q90 = quant[:, 2].tolist()
    else:
        q90 = []

    return median, q10, q90


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
        if hasattr(model, "forecast_config"):
            # New API — set horizon + quantiles
            model.forecast_config.horizon_len = (
                settings.horizon_bars
            )
            model.forecast_config.quantiles = [0.1, 0.5, 0.9]
            forecast_result = model.forecast(
                [closes], freq=[0],
            )
        else:
            forecast_result = model.forecast(
                [closes], freq=[0],
            )

        point_forecasts, quantile_forecasts = forecast_result
        point = point_forecasts[0]
        quant = quantile_forecasts[0]

        median_list, q10_list, q90_list = _extract_quantiles(
            point, quant,
        )

        median_drift = median_list[-1] - closes[-1]
        strength = min(abs(median_drift) / atr if atr > 0 else 0.0, 1.0)

        if median_drift > atr * 0.5:
            expected_direction = "UP"
        elif median_drift < -atr * 0.5:
            expected_direction = "DOWN"
        else:
            expected_direction = "FLAT"

        return Forecast(
            symbol=symbol,
            horizon_bars=settings.horizon_bars,
            timeframe=timeframe,
            median=median_list,
            q10=q10_list,
            q90=q90_list,
            expected_direction=expected_direction,  # type: ignore[arg-type]
            strength=strength,
        )
    except Exception:
        import traceback
        traceback.print_exc()
        return None
