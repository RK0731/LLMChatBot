#!/usr/bin/python3
# Author: Liu Renke
"""
This module contains customized exception classes
"""


class UserAuthenticationError(Exception):
    def __init__(self, message, status_code=403):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
    def __str__(self):
        return self.message

class InvalidRequestError(Exception):
    def __init__(self, message, status_code=480):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
    def __str__(self):
        return self.message

class IOError(Exception):
    def __init__(self, message, status_code=490):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
    def __str__(self):
        return self.message

# 500 series are used for server problems
class AppInitializationError(Exception):
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
    def __str__(self):
        return self.message
    
class UndefinedInternalError(Exception):
    """
    General class for application bug or unexpected edge cases
    """
    def __init__(self, message, status_code=510):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
    def __str__(self):
        return self.message

class UndefinedDatabaseError(Exception):
    def __init__(self, message, status_code=560):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
    def __str__(self):
        return self.message
    
class InvalidSQLError(Exception):
    def __init__(self, message, status_code=422):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
    def __str__(self):
        return self.message
    
class InvalidCypherError(Exception):
    def __init__(self, message, status_code=422):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
    def __str__(self):
        return self.message