export default function Loading({ text = "加载中..." }: { text?: string }) {
  return (
    <div className="loading-center">
      <div className="spinner spinner-lg" />
      <span>{text}</span>
    </div>
  );
}
