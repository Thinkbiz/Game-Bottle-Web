Description: Rules for unit tests in the game webapp
Globs: test_*.py
Content:
- Use unittest framework for all tests (e.g., class TestGame(unittest.TestCase)).
- Write one test method per behavior (e.g., test_template_vars_missing_keys).
- Mock external dependencies (e.g., SQLite, Bottle requests) with unittest.mock.patch.
- Name tests descriptively with purpose (e.g., test_template_complete_vars).
- Use setUp() to initialize shared state (e.g., self.template_vars = TEMPLATE_DEFAULTS.copy()).
- Assert specific conditions (e.g., self.assertRaises(ValueError, ...)).
- Keep test methods under 30 lines and focused on one outcome.
- Log test setup or failures with logger.debug/logger.error (e.g., logger.debug("Testing template vars")).
- Use in-memory SQLite (sqlite3.connect(':memory:')) for DB tests, avoiding disk I/O.
- Include type hints for test helper functions (e.g., def check_vars(vars: Dict[str, Any]) -> None).
- Test edge cases (e.g., empty dicts, invalid inputs) alongside happy paths.
