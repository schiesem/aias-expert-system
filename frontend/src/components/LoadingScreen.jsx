export default function LoadingScreen({ message = "Loading..." }) {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999,
        color: '#1f2937'
      }}
    >
      <div className="mb-8">
        <div
          className="animate-spin rounded-full h-20 w-20 border-t-4 border-b-4"
          style={{ borderTopColor: '#2196F3', borderBottomColor: '#2196F3' }}
        />
      </div>
      <h2 className="text-2xl font-semibold mb-2">{message}</h2>
      <p className="text-sm text-gray-600">Please wait while the system initializes...</p>
    </div>
  );
}
