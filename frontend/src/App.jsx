import { useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";
import UploadForm from "./components/UploadForm";

function App() {
  const handleUpload = async (formData) => {
    // Send formData to your backend API
    const response = await fetch("/api/rank-resumes", {
      method: "POST",
      body: formData,
    });
    // Handle response
  };

  return (
    <>
      <UploadForm onSubmit={handleUpload} />
    </>
  );
}

export default App;
