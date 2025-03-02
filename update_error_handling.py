import sys
import re

# New enhanced error_boundary function
NEW_ERROR_BOUNDARY = '''def error_boundary(route_func):
    """Decorator to catch and handle all errors in routes"""
    def wrapper(*args, **kwargs):
        try:
            return route_func(*args, **kwargs)
        except HTTPError as he:
            # Log HTTP errors but let them propagate to be handled by bottle's error handlers
            logger.warning(f"HTTP error in {route_func.__name__}: {str(he)}")
            raise he
        except sqlite3.Error as dbe:
            # Database errors
            logger.error(f"Database error in {route_func.__name__}: {str(dbe)}", exc_info=True)
            response.status = 500
            return template('error', 
                           error_code=500, 
                           title="Database Error", 
                           message="An unexpected database error has occurred. Our wizards have been notified!")
        except Exception as e:
            # All other errors
            logger.error(f"Unhandled exception in {route_func.__name__}: {str(e)}", exc_info=True)
            
            # Get current session info for better diagnostics
            session_id = request.get_cookie(SESSION_COOKIE_NAME, 'unknown')
            logger.error(f"Error context - Session: {session_id}, URL: {request.url}, Method: {request.method}")
            
            response.status = 500
            return template('error', 
                           error_code=500, 
                           title="Server Error", 
                           message="An unexpected error has occurred. The ancient scrolls speak of such anomalies... Our wizards have been notified!")
    return wrapper'''

# Regular expression to match the existing error_boundary function
ERROR_BOUNDARY_PATTERN = r'def error_boundary\(route_func\):[\s\S]*?return wrapper'

def update_file(file_path):
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace the error_boundary function
        updated_content = re.sub(ERROR_BOUNDARY_PATTERN, NEW_ERROR_BOUNDARY, content)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(updated_content)
        
        print(f"Successfully updated error handling in {file_path}")
        return True
    except Exception as e:
        print(f"Error updating file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_error_handling.py <path_to_web_game.py>")
        sys.exit(1)
    
    success = update_file(sys.argv[1])
    sys.exit(0 if success else 1) 