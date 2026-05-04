import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { IncidentService } from '../../core/services/incident';
import { Incident, IncidentType, IncidentStatus } from '../../core/models/incident.model';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-incidents',
  standalone: false,
  templateUrl: './incidents.html',
  styleUrl: './incidents.css',
})
export class Incidents implements OnInit, OnDestroy {
  incidents: Incident[] = [];
  filteredIncidents: Incident[] = [];
  isLoading = true;
  loadError: string | null = null;
  
  filterType: string = 'ALL';
  filterStatus: string = 'ALL';
  
  private refreshSubscription?: Subscription;

  constructor(
    private incidentService: IncidentService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadIncidents();
    // Refresh every 10 seconds
    this.refreshSubscription = interval(10000).subscribe(() => {
      this.loadIncidents();
    });
  }

  ngOnDestroy(): void {
    this.refreshSubscription?.unsubscribe();
  }

  loadIncidents(): void {
    this.loadError = null;
    this.incidentService.getIncidents().subscribe({
      next: (incidents) => {
        this.incidents = incidents;
        this.applyFilters();
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading incidents:', err);
        this.incidents = [];
        this.filteredIncidents = [];
        this.loadError =
          'Could not load incidents. Check that the API is reachable and you are still logged in.';
        this.isLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  applyFilters(): void {
    this.filteredIncidents = this.incidents.filter(incident => {
      const typeMatch = this.filterType === 'ALL' || incident.incident_type === this.filterType;
      const statusMatch = this.filterStatus === 'ALL' || incident.status === this.filterStatus;
      return typeMatch && statusMatch;
    });
  }

  onFilterChange(): void {
    this.applyFilters();
  }
}

