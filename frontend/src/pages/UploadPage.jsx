import { useNavigate } from "react-router-dom";
import UploadForm from "../components/UploadForm";

const UploadPage = () => {
  const navigate = useNavigate();

  const handleUpload = async (formData) => {
    const response = await fetch("/api/rank-resumes", {
      method: "POST",
      body: formData,
    });
    // Handle response:  navigate("/results");
  };
  return <UploadForm onSubmit={handleUpload} />;
};

export default UploadPage;
