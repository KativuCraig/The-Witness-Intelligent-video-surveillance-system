import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { TOKEN_KEY } from '../interceptors/auth.interceptor';

export interface LoginUser {
  id: number;
  username: string;
  role: string;
}

export interface LoginResponse {
  token: string;
  user: LoginUser;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  constructor(private http: HttpClient) {}

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  isLoggedIn(): boolean {
    return !!this.token;
  }

  async login(username: string, password: string): Promise<LoginResponse> {
    const res = await firstValueFrom(
      this.http.post<LoginResponse>(`${environment.apiUrl}/auth/login/`, {
        username,
        password,
      })
    );
    localStorage.setItem(TOKEN_KEY, res.token);
    return res;
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
  }
}
