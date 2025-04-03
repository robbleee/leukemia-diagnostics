    
    # Display results if available in session state
    if 'ipss_results' in st.session_state:
        results = st.session_state['ipss_results']
        
        # Get the results data
        ipssr_result = results['ipssr_result']
        ipssm_result = results['ipssm_result']
        survival_data = results.get('survival_data', {})
        
        # Display results header
        st.markdown(
            """
            <div style="
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
                margin-bottom: 20px;
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
                ">
                <h2 style="color: #009688; text-align: left;">
                    Risk Assessment Results
                </h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Create tabs for IPSS-M and IPSS-R, matching the display in show_ipss_risk_assessment
        ipss_tabs = st.tabs(["IPSS-M", "IPSS-R"])
        
        # ------------------- IPSS-M TAB -------------------
        with ipss_tabs[0]:
            risk_category_m = ipssm_result.get("means", {}).get("risk_cat", "Unknown")
            risk_class_m = risk_category_m.lower().replace(" ", "-") + "-risk" if risk_category_m else "moderate-risk"
            
            st.markdown(f"""
            <div class='risk-box {risk_class_m}'>
                <div class='risk-title'>IPSS-M Risk</div>
                <div class='risk-value'>{risk_category_m}</div>
                <div class='risk-os'>Score: {ipssm_result.get("means", {}).get("risk_score", "N/A")}</div>
                <div class='risk-os'>Median OS: {survival_data.get("median_os", "N/A")}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("IPSS-M Details", expanded=False):
                st.markdown("### IPSS-M Risk Details")
                st.markdown(f"- **Risk Category**: {risk_category_m}")
                st.markdown(f"- **Total Score**: {ipssm_result.get("means", {}).get("risk_score", "N/A")}")
                st.markdown(f"- **Median Overall Survival**: {survival_data.get("median_os", "N/A")}")
                st.markdown(f"- **2-Year Survival Probability**: {survival_data.get("survival_2yr", "N/A")}")
                st.markdown(f"- **5-Year Survival Probability**: {survival_data.get("survival_5yr", "N/A")}")
                
                # Show mutation impact if available
                if 'mutation_scores' in ipssm_result:
                    st.markdown("### Genetic Mutation Impact")
                    for mutation, score in ipssm_result['mutation_scores'].items():
                        if score != 0:
                            st.markdown(f"- **{mutation}**: {score} points")
        
        # Display the original data for transparency
        with st.expander("Data Inspector - IPSS Data", expanded=False):
            st.subheader("Original Data Used for IPSS Classification")
            if 'ipss_data' in results:
                st.json(results['ipss_data'])
            else:
                st.info("Original data not available for inspection.")
        
        # Clear results button
        if st.button("Clear Results and Start Over"):
            # Remove the results from session state
