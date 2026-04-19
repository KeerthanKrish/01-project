import { Request, Response, NextFunction } from 'express';

/**
 * Authentication middleware to verify Bearer token
 */
export function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({
      error: 'Unauthorized',
      message: 'Missing or invalid Authorization header. Expected: Bearer <token>',
    });
    return;
  }

  const token = authHeader.substring(7); // Remove 'Bearer ' prefix
  const expectedToken = process.env.AUTH_TOKEN;

  if (!expectedToken) {
    console.error('AUTH_TOKEN not configured in environment');
    res.status(500).json({
      error: 'Server Configuration Error',
      message: 'Authentication not properly configured',
    });
    return;
  }

  if (token !== expectedToken) {
    res.status(403).json({
      error: 'Forbidden',
      message: 'Invalid authentication token',
    });
    return;
  }

  next();
}

/**
 * Error handling middleware
 */
export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  console.error('Error:', err);

  res.status(500).json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'An error occurred',
  });
}
