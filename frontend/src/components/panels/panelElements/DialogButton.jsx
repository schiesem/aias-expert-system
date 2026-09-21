export default function DialogButton({label, onClick, isDisabled}) {
    const buttonClass = `
    w-12 h-8 flex items-center justify-center text-sm text-center px-4 py-2 shadow-md rounded-md bg-white border border-stone-400 hover:bg-stone-100 transition ${
      isDisabled
        ? "bg-gray-300 border-gray-400 text-gray-600 cursor-not-allowed opacity-50"
        : "bg-white border-stone-400 hover:bg-stone-100"
    }`

  return (
    <div className="flex justify-between items-center gap-x-4">
      <span className="text-sm">{label}</span>
      <button className={buttonClass} onClick={onClick} disabled={isDisabled}></button>
    </div>
  );
}
