import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, RefresherCustomEvent } from '@ionic/angular';
import { AuthService } from '../services/auth.service';
import { AlertItem, AlertsService } from '../services/alerts.service';
import { AlarmService } from '../services/alarm.service';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-home',
  templateUrl: 'home.page.html',
  styleUrls: ['home.page.scss'],
  standalone: false,
})
export class HomePage implements OnDestroy {
  alerts: AlertItem[] = [];
  loading = false;
  error: string | null = null;
  apiUrl = environment.apiUrl;
  private pollId: ReturnType<typeof setInterval> | null = null;
  /** After first fetch, new alert IDs trigger the alarm */
  private readonly knownAlertIds = new Set<number>();
  private baselineEstablished = false;

  constructor(
    private alertsService: AlertsService,
    public alarm: AlarmService,
    private auth: AuthService,
    private router: Router,
    private alertCtrl: AlertController
  ) {}

  async ionViewWillEnter(): Promise<void> {
    this.knownAlertIds.clear();
    this.baselineEstablished = false;
    await this.loadAlerts(true);
    this.startPolling();
  }

  ionViewWillLeave(): void {
    this.stopPolling();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  private startPolling(): void {
    this.stopPolling();
    this.pollId = setInterval(() => void this.loadAlerts(false), 10000);
  }

  private stopPolling(): void {
    if (this.pollId !== null) {
      clearInterval(this.pollId);
      this.pollId = null;
    }
  }

  async loadAlerts(showSpinner: boolean): Promise<void> {
    this.error = null;
    if (showSpinner) {
      this.loading = true;
    }
    try {
      this.alerts = await this.alertsService.list();
      this.detectNewAlerts(this.alerts);
    } catch (e: unknown) {
      this.error =
        e && typeof e === 'object' && 'message' in e
          ? String((e as { message: string }).message)
          : 'Could not load alerts';
    } finally {
      this.loading = false;
    }
  }

  stopAlarm(): void {
    this.alarm.stop();
  }

  private detectNewAlerts(items: AlertItem[]): void {
    if (!this.baselineEstablished) {
      for (const a of items) {
        this.knownAlertIds.add(a.id);
      }
      this.baselineEstablished = true;
      return;
    }
    let anyNew = false;
    for (const a of items) {
      if (!this.knownAlertIds.has(a.id)) {
        this.knownAlertIds.add(a.id);
        anyNew = true;
      }
    }
    if (anyNew) {
      void this.alarm.start();
    }
  }

  async doRefresh(ev: RefresherCustomEvent): Promise<void> {
    await this.loadAlerts(false);
    (ev.target as HTMLIonRefresherElement).complete();
  }

  async logout(): Promise<void> {
    const alert = await this.alertCtrl.create({
      header: 'Sign out?',
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Sign out',
          handler: () => {
            this.alarm.stop();
            this.auth.logout();
            void this.router.navigateByUrl('/login', { replaceUrl: true });
          },
        },
      ],
    });
    await alert.present();
  }

  /** Backend may omit until upgraded; default to NEW. */
  statusOf(a: AlertItem): string {
    return a.incident_status || 'NEW';
  }

  async confirmAlert(a: AlertItem): Promise<void> {
    try {
      await this.alertsService.confirm(a.incident);
      await this.loadAlerts(false);
    } catch (e: unknown) {
      await this.errToast(e, 'Could not confirm');
    }
  }

  async dismissAlert(a: AlertItem): Promise<void> {
    try {
      await this.alertsService.dismiss(a.incident);
      await this.loadAlerts(false);
    } catch (e: unknown) {
      await this.errToast(e, 'Could not dismiss');
    }
  }

  private async errToast(e: unknown, fallback: string): Promise<void> {
    let msg = fallback;
    if (e instanceof HttpErrorResponse) {
      const body = e.error;
      if (body && typeof body === 'object' && 'detail' in body) {
        const d = (body as { detail: unknown }).detail;
        if (typeof d === 'string') {
          msg = d;
        }
      } else if (e.message) {
        msg = e.message;
      }
    } else if (e && typeof e === 'object' && 'message' in e) {
      const m = (e as { message?: string }).message;
      if (typeof m === 'string' && m) {
        msg = m;
      }
    }
    const t = await this.alertCtrl.create({
      header: 'Error',
      message: msg,
      buttons: ['OK'],
    });
    await t.present();
  }
}
