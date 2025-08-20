<script setup lang="ts">
/**
 * Компонент для отображения аватара пользователя в разделе "Данные аккаунта" в
 * "Личном кабинете". Отображает серый значок пользователя.
 */
</script>

<template>
  <svg
    viewBox="0 0 75 75"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    class="account-icon"
  >
    <g filter="url(#filter0_d_513_3609)">
      <circle
        cx="37.5"
        cy="36.5"
        r="30.5"
        fill="currentColor"
      />
      <circle
        cx="37.5"
        cy="36.5"
        r="33"
        stroke="white"
        stroke-width="5"
      />
    </g>
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M44.5138 30.229C44.5138 33.8993 41.5384 36.8746 37.8681 36.8746C34.1979 36.8746 31.2225 33.8993 31.2225 30.229C31.2225 26.5587 34.1979 23.5834 37.8681 23.5834C41.5384 23.5834 44.5138 26.5587 44.5138 30.229ZM28.82 49.5653H46.9162C48.6212 49.5653 50.0162 48.6159 50.0162 47.4534V47.1046C50.0162 42.4546 44.165 38.6959 37.5 38.8315C30.835 38.9671 25.72 42.9196 25.72 47.4534C25.72 48.6159 27.115 49.5653 28.82 49.5653Z"
      fill="white"
    />
    <defs>
      <filter
        id="filter0_d_513_3609"
        x="0.5"
        y="0.5"
        width="74"
        height="74"
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
        <feOffset dy="1" />
        <feGaussianBlur stdDeviation="0.75" />
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
</style>
