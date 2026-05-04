import { HttpInterceptorFn } from '@angular/common/http';

export const TOKEN_KEY = 'gods_eye_auth_token';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Token ${token}` },
    });
  }
  return next(req);
};
