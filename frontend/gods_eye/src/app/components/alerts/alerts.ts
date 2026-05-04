import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { AlertService } from '../../core/services/alert';
import { Auth } from '../../core/services/auth';
import { IncidentService } from '../../core/services/incident';
import { Alert } from '../../core/models/alert.model';
import { IncidentStatus } from '../../core/models/incident.model';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-alerts',
  standalone: false,
  templateUrl: './alerts.html',
  styleUrl: './alerts.css',
})
export class Alerts implements OnInit, OnDestroy {
  alerts: Alert[] = [];
  isLoading = true;
  /** Shown when the alerts API request fails (otherwise the template could render nothing useful). */
  loadError: string | null = null;
  actionError: string | null = null;
  private refreshSubscription?: Subscription;

  constructor(
    private alertService: AlertService,
    private incidentService: IncidentService,
    private cdr: ChangeDetectorRef,
    public auth: Auth
  ) {}

  ngOnInit(): void {
    this.loadAlerts();
    // Refresh every 5 seconds
    this.refreshSubscription = interval(5000).subscribe(() => {
      this.loadAlerts();
    });
  }

  ngOnDestroy(): void {
    this.refreshSubscription?.unsubscribe();
  }

  loadAlerts(): void {
    this.loadError = null;
    this.alertService.getAlerts().subscribe({
      next: (alerts) => {
        this.alerts = Array.isArray(alerts) ? alerts : [];
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading alerts:', err);
        this.alerts = [];
        this.loadError =
          'Could not load alerts. Check that the backend is running, the API URL in `api.config.ts` is correct, and you are still logged in.';
        this.isLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  typeBadgeClass(alert: Alert): string {
    return (alert.incident_type || 'VIOLENCE').toLowerCase();
  }

  statusOf(alert: Alert): IncidentStatus {
    return alert.incident_status ?? 'NEW';
  }

  confirmAlert(alert: Alert): void {
    this.actionError = null;
    this.incidentService.confirmIncident(alert.incident).subscribe({
      next: (inc) => this.patchAlertStatus(alert.id, inc.status as IncidentStatus),
      error: () => {
        this.actionError = 'Could not confirm this alert. You may lack permission or the incident was already closed.';
        this.cdr.detectChanges();
      },
    });
  }

  dismissAlert(alert: Alert): void {
    this.actionError = null;
    this.incidentService.dismissIncident(alert.incident).subscribe({
      next: (inc) => this.patchAlertStatus(alert.id, inc.status as IncidentStatus),
      error: () => {
        this.actionError = 'Could not dismiss this alert.';
        this.cdr.detectChanges();
      },
    });
  }

  private patchAlertStatus(alertId: number, status: IncidentStatus): void {
    const i = this.alerts.findIndex((a) => a.id === alertId);
    if (i >= 0) {
      this.alerts[i] = { ...this.alerts[i], incident_status: status };
    }
    this.cdr.detectChanges();
  }
}

