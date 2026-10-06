// The look of the buttons, in one place. It is a function that returns Tailwind classes (not a component), so
// it works on a <button> and on a <Link> alike:
//
//   <button className={buttonClass("primary")}>Save</button>
//   <Link href="/contacts" className={buttonClass("secondary")}>Contacts</Link>

const base = "cursor-pointer rounded-md text-sm disabled:cursor-not-allowed disabled:opacity-50";

const variants = {
  primary: "bg-blue-600 text-white",
  secondary: "border border-zinc-300 dark:border-zinc-700",
  danger: "border border-red-300 text-red-700 dark:border-red-800 dark:text-red-400",
};

const sizes = {
  normal: "px-4 py-2",
  small: "px-3 py-1", // the buttons inside a table or a list row
};

export function buttonClass(variant: keyof typeof variants, size: keyof typeof sizes = "normal") {
  return `${base} ${variants[variant]} ${sizes[size]}`;
}
