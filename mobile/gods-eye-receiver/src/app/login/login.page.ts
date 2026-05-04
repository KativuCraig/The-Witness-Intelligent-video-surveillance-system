import { Component } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { AlertController, LoadingController } from '@ionic/angular';
import { AuthService } from '../services/auth.service';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
  standalone: false,
})
export class LoginPage {
  username = '';
  password = '';

  constructor(
    private auth: AuthService,
    private router: Router,
    private loadingCtrl: LoadingController,
    private alertCtrl: AlertController
  ) {}

  async ionViewWillEnter(): Promise<void> {
    if (this.auth.isLoggedIn()) {
      await this.router.navigateByUrl('/home', { replaceUrl: true });
    }
  }

  async submit(): Promise<void> {
    const loading = await this.loadingCtrl.create({ message: 'Signing in…' });
    await loading.present();
    try {
      await this.auth.login(this.username.trim(), this.password);
      await this.router.navigateByUrl('/home', { replaceUrl: true });
    } catch (e: unknown) {
      let msg = 'Login failed. Check API URL and that the server is running.';
      if (e instanceof HttpErrorResponse) {
        if (e.status === 0) {
          msg = `Cannot reach backend at ${environment.apiUrl}. Ensure backend is running and accessible from this device.`;
        } else if (typeof e.error === 'string') {
          msg = e.error;
        } else if (e.error && typeof e.error === 'object') {
          msg = (e.error as { detail?: string }).detail ?? JSON.stringify(e.error);
        } else {
          msg = `Login failed (HTTP ${e.status}).`;
        }
      }
      const alert = await this.alertCtrl.create({
        header: 'Login error',
        message: msg,
        buttons: ['OK'],
      });
      await alert.present();
    } finally {
      await loading.dismiss();
    }
  }
}
