# pycaldera

Python client library for controlling Caldera spas via their cloud API.

## Installation

```bash
pip install pycaldera
```

## Usage

### Asynchronous API

```python
import asyncio
from pycaldera import AsyncCalderaClient, PUMP_OFF, PUMP_LOW, PUMP_HIGH


async def main():
    async with AsyncCalderaClient("email@example.com", "password") as spa:
        # Get current spa status
        status = await spa.get_spa_status()
        print(f"Current temperature: {status.ctrl_head_water_temperature}°F")

        # Get detailed live settings
        settings = await spa.get_live_settings()
        print(f"Target temperature: {settings.ctrl_head_set_temperature}°F")

        # Control the spa
        await spa.set_temperature(102)  # Set temperature to 102°F
        await spa.set_pump(1, PUMP_HIGH)  # Set pump 1 to high speed
        await spa.set_lights(True)  # Turn on the lights


asyncio.run(main())
```

### Synchronous API

For simpler use cases, a synchronous wrapper is also available:

```python
from pycaldera import CalderaClient, PUMP_OFF, PUMP_LOW, PUMP_HIGH

with CalderaClient("email@example.com", "password") as spa:
    # Get current spa status
    status = spa.get_spa_status()
    print(f"Current temperature: {status.ctrl_head_water_temperature}°F")

    # Get detailed live settings
    settings = spa.get_live_settings()
    print(f"Target temperature: {settings.ctrl_head_set_temperature}°F")

    # Control the spa
    spa.set_temperature(102)  # Set temperature to 102°F
    spa.set_pump(1, PUMP_HIGH)  # Set pump 1 to high speed
    spa.set_lights(True)  # Turn on the lights
```

Both clients provide identical functionality, with the synchronous client simply wrapping the async one for convenience.

## API Reference

### AsyncCalderaClient

The main async client class for interacting with the spa. All operations must be performed within an async context manager:

```python
async with AsyncCalderaClient(
    email="email@example.com",
    password="password",
    timeout=10.0,  # Optional: request timeout in seconds
    debug=False,  # Optional: enable debug logging
) as spa:
    # All spa operations must be inside this block
    await spa.get_spa_status()
    await spa.set_temperature(102)
    # etc...
```

### CalderaClient

A synchronous wrapper around AsyncCalderaClient that provides the same functionality without requiring async/await:

```python
with CalderaClient(
    email="email@example.com",
    password="password",
    timeout=10.0,  # Optional: request timeout in seconds
    debug=False,  # Optional: enable debug logging
) as spa:
    # All spa operations can be called synchronously
    spa.get_spa_status()
    spa.set_temperature(102)
    # etc...
```

### Error Handling

All operations can raise these base exceptions:
- `AuthenticationError`: When authentication fails or token expires
- `ConnectionError`: When network connection fails or API is unreachable
- `SpaControlError`: When the API returns an error response

### Temperature Control

```python
async with spa as client:
    # Set temperature (80-104°F or 26.5-40°C)
    try:
        # Basic temperature setting
        await client.set_temperature(102)  # Fahrenheit
        await client.set_temperature(39, "C")  # Celsius

        # Wait for spa to acknowledge the temperature change
        await client.set_temperature(102, wait_for_ack=True)

        # Control polling behavior when waiting for acknowledgment
        await client.set_temperature(
            102,
            wait_for_ack=True,
            polling_interval=5.0,  # Check every 5 seconds
            polling_timeout=120.0,  # Time out after 2 minutes
        )

        # Manually wait for temperature acknowledgment
        settings = await client.wait_for_temperature_ack(
            expected_temp=102,  # Expected temperature in Fahrenheit
            interval=5.0,  # Check every 5 seconds
            timeout=120.0,  # Time out after 2 minutes
        )
    except InvalidParameterError:
        # Raised when temperature is outside valid range
        # (80-104°F or 26.5-40°C)
        pass
    except SpaControlError:
        # Raised when polling times out waiting for acknowledgment
        pass
```

### Pump Control

```python
async with spa as client:
    try:
        await client.set_pump(1, PUMP_HIGH)  # Set pump 1 to high speed
        await client.set_pump(2, PUMP_LOW)  # Set pump 2 to low speed
        await client.set_pump(3, PUMP_OFF)  # Turn off pump 3
    except InvalidParameterError:
        # Raised when:
        # - pump_number is not 1, 2, or 3
        # - speed is not PUMP_OFF (0), PUMP_LOW (1), or PUMP_HIGH (2)
        pass
```

### Light Control

```python
async with spa as client:
    try:
        await client.set_lights(True)  # Turn lights on
        await client.set_lights(False)  # Turn lights off
    except SpaControlError:
        # Raised when light control fails
        pass
```

### Status & Settings

```python
async with spa as client:
    try:
        # Get basic spa status
        status = await client.get_spa_status()
        print(f"Online: {status.status == 'ONLINE'}")

        # Get detailed live settings
        settings = await client.get_live_settings()
        print(f"Target temp: {settings.ctrl_head_set_temperature}°F")
    except ConnectionError:
        # Raised when spa is offline or unreachable
        pass
    except SpaControlError:
        # Raised when API returns invalid data
        pass

## Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

The pre-commit hooks will run automatically on git commit, checking:
- Code formatting (Black)
- Import sorting (isort)
- Type checking (mypy)
- Linting (pylint, ruff)
- YAML/TOML syntax
- Trailing whitespace and file endings

## License

MIT License - see LICENSE file for details.
