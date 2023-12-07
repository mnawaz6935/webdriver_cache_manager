# webdriver_cache_manager

`webdriver_cache_manager` simplifies managing ChromeDriver instances in Selenium using Python. Track active processes, terminate unused instances, and handle associated PIDs with ease.

[![Upload Python Package](https://github.com/mnawaz6935/webdriver_cache_manager/actions/workflows/python-publish.yml/badge.svg?branch=main)](https://github.com/mnawaz6935/webdriver_cache_manager/actions/workflows/python-publish.yml)
## Installation

Install via pip:

```bash
pip install webdriver_cache_manager
```


## Features

- **Process Tracking:** Monitor active ChromeDriver instances.
- **Termination:** Safely terminate unused ChromeDriver processes.
- **CSV Management:** Handle PIDs efficiently using CSV files.
  
## Usage

1. **Import Package:**
    ```python
    from webdriver_cache_manager import ManageChromeDriverCache
    ```

   2. **Initialize Manager:**
      - Create a `Chrome Driver` instance.
      - Utilize the methods for managing ChromeDriver instances.
      - ````python
         ManageChromeDriverCache(driver)
         ````

## Examples

Check out the provided examples and utilities for managing ChromeDriver instances in the `examples` directory.

## Contributions

Contributions are welcome! If you encounter issues or have suggestions, feel free to create an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
