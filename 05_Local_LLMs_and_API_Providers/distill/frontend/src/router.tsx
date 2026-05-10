import { createBrowserRouter } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import InputPage from "./pages/InputPage";
import SummaryPage from "./pages/SummaryPage";
import AssessmentPage from "./pages/AssessmentPage";
import ResultsPage from "./pages/ResultsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <InputPage /> },
      { path: "summary", element: <SummaryPage /> },
      { path: "assessment", element: <AssessmentPage /> },
      { path: "results", element: <ResultsPage /> },
    ],
  },
]);
