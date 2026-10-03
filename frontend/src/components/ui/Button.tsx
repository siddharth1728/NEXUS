"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "success";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "secondary", size = "md", isLoading = false, children, disabled, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent disabled:pointer-events-none disabled:opacity-50 select-none cursor-pointer";

    const variantStyles = {
      primary: "bg-[#2563EB] text-white hover:bg-[#1D4ED8] shadow-xs active:bg-[#1E40AF]",
      secondary: "bg-white text-[#171717] border border-[#E5E7EB] hover:bg-[#F2F2F0] hover:border-[#D1D5DB] active:bg-[#EBEBE8]",
      outline: "border border-[#E5E7EB] bg-transparent text-[#171717] hover:bg-[#F2F2F0]",
      ghost: "text-[#5F6368] hover:text-[#171717] hover:bg-[#F2F2F0]",
      danger: "bg-[#C62828] text-white hover:bg-[#B71C1C] shadow-xs",
      success: "bg-[#17803D] text-white hover:bg-[#157336] shadow-xs",
    };

    const sizeStyles = {
      sm: "h-7 px-2.5 text-xs rounded-[5px] gap-1.5",
      md: "h-8 px-3.5 text-xs rounded-[6px] gap-2",
      lg: "h-9 px-4 text-sm rounded-[6px] gap-2",
      icon: "h-8 w-8 rounded-[6px] p-0 flex items-center justify-center",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        {...props}
      >
        {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
