import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { Login } from './components/login/login';
import { Dashboard } from './components/dashboard/dashboard';
import { Cameras } from './components/cameras/cameras';
import { CameraForm } from './components/camera-form/camera-form';
import { CameraMonitor } from './components/camera-monitor/camera-monitor';
import { Processing } from './components/processing/processing';
import { Incidents } from './components/incidents/incidents';
import { IncidentDetail } from './components/incident-detail/incident-detail';
import { Evidence } from './components/evidence/evidence';
import { Alerts } from './components/alerts/alerts';
import { authGuard } from './core/guards/auth-guard';
import { roleGuard } from './core/guards/role-guard';

const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: Login },
  { 
    path: 'dashboard', 
    component: Dashboard,
    canActivate: [authGuard]
  },
  { 
    path: 'cameras', 
    component: Cameras,
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN'] }
  },
  { 
    path: 'cameras/new', 
    component: CameraForm,
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN'] }
  },
  { 
    path: 'cameras/monitor', 
    component: CameraMonitor,
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN'] }
  },
  {
    path: 'processing/:id',
    component: Processing,
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN'] }
  },
  { 
    path: 'incidents', 
    component: Incidents,
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN', 'SECURITY'] }
  },
  { 
    path: 'incidents/:id', 
    component: IncidentDetail,
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN', 'SECURITY'] }
  },
  { 
    path: 'evidence', 
    component: Evidence,
    canActivate: [authGuard, roleGuard],
    data: { roles: ['SECURITY'] }
  },
  { 
    path: 'alerts', 
    component: Alerts,
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN', 'SECURITY', 'VIEWER'] }
  },
  { path: '**', redirectTo: '/dashboard' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

