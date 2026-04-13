/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./pages/**/*.{pyxl,js,jsx,ts,tsx}",
        "./.pyxle-build/client/pages/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {},
    },
    plugins: [],
};
