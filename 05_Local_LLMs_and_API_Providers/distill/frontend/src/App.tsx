import { RouterProvider } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import { router } from "./router";

export default function App() {
  return (
    <AppProvider>
      <RouterProvider router={router} />
    </AppProvider>
  );
}
