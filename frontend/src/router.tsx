import { createBrowserRouter, Navigate } from "react-router-dom";

import ProtectedRoute from "@/auth/ProtectedRoute";
import ApplicationDetailPage from "@/pages/ApplicationDetailPage";
import ApplicationFormPage from "@/pages/ApplicationFormPage";
import ApplicationStatusPage from "@/pages/ApplicationStatusPage";
import AnalyticsDashboardPage from "@/pages/AnalyticsDashboardPage";
import DashboardPage from "@/pages/DashboardPage";
import LoginPage from "@/pages/LoginPage";
import NotFoundPage from "@/pages/NotFoundPage";
import RegisterPage from "@/pages/RegisterPage";
import StaffDashboardPage from "@/pages/StaffDashboardPage";
import UnauthorizedPage from "@/pages/UnauthorizedPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/register",
    element: <RegisterPage />,
  },
  {
    path: "/unauthorized",
    element: <UnauthorizedPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: "/",
        element: <DashboardPage />,
      },
      {
        path: "/applications/:id",
        element: <ApplicationDetailPage />,
      },
    ],
  },
  {
    element: <ProtectedRoute allowedRoles={["applicant"]} />,
    children: [
      {
        path: "/apply",
        element: <ApplicationFormPage />,
      },
      {
        path: "/applications",
        element: <ApplicationStatusPage />,
      },
    ],
  },
  {
    element: <ProtectedRoute allowedRoles={["staff", "admin"]} />,
    children: [
      {
        path: "/staff/applications",
        element: <StaffDashboardPage />,
      },
      {
        path: "/staff/analytics",
        element: <AnalyticsDashboardPage />,
      },
    ],
  },
  {
    path: "/404",
    element: <NotFoundPage />,
  },
  {
    path: "*",
    element: <Navigate to="/404" replace />,
  },
]);