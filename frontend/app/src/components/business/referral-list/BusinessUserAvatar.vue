<script setup lang="ts">
/**
 * Компонент для отображения аватара пользователя в модалке "Все приглашенные
 * пользователи" в разделе "Бизнес". Отображает значок пользователя.
 */
</script>

<template>
  <svg
    viewBox="0 0 26 26"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    class="account-icon"
  >
    <g filter="url(#filter0_d_513_3609)">
      <circle
        cx="13"
        cy="12.67"
        r="10.57"
        fill="currentColor"
      />
      <circle
        cx="13"
        cy="12.67"
        r="11.44"
        stroke="white"
        stroke-width="1.73"
      />
    </g>
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M15.43 10.48C15.43 11.75 14.38 12.8 13.11 12.8C11.84 12.8 10.79 11.75 10.79 10.48C10.79 9.21 11.84 8.16 13.11 8.16C14.38 8.16 15.43 9.21 15.43 10.48ZM9.99 17.17H16.24C16.89 17.17 17.34 16.85 17.34 16.44V16.26C17.34 14.73 15.31 13.38 13 13.43C10.69 13.48 8.91 14.89 8.91 16.44C8.91 16.85 9.36 17.17 9.99 17.17Z"
      fill="white"
    />
    <defs>
      <filter
        id="filter0_d_513_3609"
        x="0.17"
        y="0.17"
        width="25.66"
        height="25.66"
        filterUnits="userSpaceOnUse"
        color-interpolation-filters="sRGB"
      >
        <feFlood
          flood-opacity="0"
          result="BackgroundImageFix"
        />
        <feColorMatrix
          in="SourceAlpha"
          type="matrix"
          values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
          result="hardAlpha"
        />
        <feOffset dy="0.35" />
        <feGaussianBlur stdDeviation="0.26" />
        <feComposite
          in2="hardAlpha"
          operator="out"
        />
        <feColorMatrix
          type="matrix"
          values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"
        />
        <feBlend
          mode="normal"
          in2="BackgroundImageFix"
          result="effect1_dropShadow_513_3609"
        />
        <feBlend
          mode="normal"
          in="SourceGraphic"
          in2="effect1_dropShadow_513_3609"
          result="shape"
        />
      </filter>
    </defs>
  </svg>
</template>

<style scoped>
@import "@/assets/styles/profile.css";

.account-icon {
  width: 32px !important;
  height: 32px !important;
}
</style>
