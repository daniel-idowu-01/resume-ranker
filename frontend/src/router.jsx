import { ResultsPage } from "./pages";
import UploadPage from "./pages/UploadPage";
import { createBrowserRouter } from "react-router-dom";

const router = createBrowserRouter([
  {
    path: "/",
    element: <UploadPage />,
  },
  {
    path: "/results/:id",
    element: <ResultsPage />,
  },
]);

export default router;
