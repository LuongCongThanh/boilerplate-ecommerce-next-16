import localFont from 'next/font/local';

export const circularStd = localFont({
  src: [
    {
      path: '../public/fonts/SFPRODISPLAYBLACKITALIC.OTF',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../public/fonts/SFPRODISPLAYBOLD.OTF',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../public/fonts/SFPRODISPLAYMEDIUM.OTF',
      weight: '500',
      style: 'normal',
    },
    {
      path: '../public/fonts/SFPRODISPLAYREGULAR.OTF.OTF',
      weight: '450',
      style: 'normal',
    },
  ],
  variable: '--font-SFPRODISPLAYREGULAR', // Optional: For CSS custom properties
  display: 'swap', // Use 'swap' to avoid font-blocking issues
});
