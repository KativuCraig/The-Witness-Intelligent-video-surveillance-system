import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Auth } from '../services/auth';

export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(Auth);
  const router = inject(Router);
  
  const requiredRoles = route.data['roles'] as string[];
  
  if (authService.hasRole(requiredRoles)) {
    return true;
  }
  
  router.navigate(['/dashboard']);
  return false;
};

