import { Component, OnInit } from '@angular/core';
import { Auth } from '../../core/services/auth';
import { User } from '../../core/models/user.model';

@Component({
  selector: 'app-navbar',
  standalone: false,
  templateUrl: './navbar.html',
  styleUrl: './navbar.css',
})
export class Navbar implements OnInit {
  currentUser: User | null = null;

  constructor(public authService: Auth) {}

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });
  }

  logout(): void {
    this.authService.logout();
  }

  hasRole(roles: string[]): boolean {
    return this.authService.hasRole(roles);
  }
}

