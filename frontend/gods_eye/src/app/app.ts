import { Component, OnInit } from '@angular/core';
import { Auth } from './core/services/auth';
import { Router } from '@angular/router';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  standalone: false,
  styleUrl: './app.css'
})
export class App implements OnInit {
  showNavbar = false;

  constructor(
    public authService: Auth,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.router.events.subscribe(() => {
      this.showNavbar = this.authService.isAuthenticated() && 
                       this.router.url !== '/login';
    });
  }
}

