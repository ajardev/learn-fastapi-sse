import React, { useState, useEffect } from "react";

const Stepper = () => {
  const [steps, setSteps] = useState([
    { id: 1, title: "Validasi Input", status: "pending" },
    { id: 2, title: "Proses Data", status: "pending" },
    { id: 3, title: "Simpan ke Database", status: "pending" },
    { id: 4, title: "Kirim Notifikasi", status: "pending" },
  ]);
  const [currentProcess, setCurrentProcess] = useState(null);
  const [error, setError] = useState(null);

  const startProcess = () => {
    // Reset status
    setSteps(steps.map((step) => ({ ...step, status: "pending" })));
    setError(null);

    // Mulai proses dan listen untuk updates
    const eventSource = new EventSource("http://localhost:8000/api/process");

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "step_update") {
        setSteps((prevSteps) =>
          prevSteps.map((step) =>
            step.id === data.step_id ? { ...step, status: data.status } : step,
          ),
        );
      } else if (data.type === "process_complete") {
        eventSource.close();
      } else if (data.type === "error") {
        setError(data.message);
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      setError("Koneksi terputus");
      eventSource.close();
    };

    // Simpan referensi ke eventSource untuk cleanup
    setCurrentProcess(eventSource);
  };

  // Cleanup eventSource ketika komponen unmount
  useEffect(() => {
    return () => {
      if (currentProcess) {
        currentProcess.close();
      }
    };
  }, [currentProcess]);

  return (
    <div className="stepper-container">
      <h2>Proses Data</h2>

      <div className="steps">
        {steps.map((step) => (
          <div key={step.id} className={`step-item ${step.status}`}>
            <div className="step-number">{step.id}</div>
            <div className="step-content">
              <div className="step-title">{step.title}</div>
              <div className="step-status">
                {step.status === "pending" && "Menunggu"}
                {step.status === "processing" && "Sedang diproses..."}
                {step.status === "completed" && "Selesai"}
                {step.status === "failed" && "Gagal"}
              </div>
            </div>
          </div>
        ))}
      </div>

      {error && <div className="error-message">{error}</div>}

      <button onClick={startProcess} disabled={currentProcess !== null}>
        Mulai Proses
      </button>
    </div>
  );
};

export default Stepper;
