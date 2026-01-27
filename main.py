import src.ciallo
from src.basellm import BaseLLM
from src.llm import LLM
from src.framework import Framework
from src.analysis import Analysis
from prog_params import ProgParams as prog_params
#from src.ciallo import Ciallo
from user_params import UserParams as user_params

def main(framework=None, project=None, bug_ids=None, repair_tool=None, model=user_params.MODEL):

    defects4j = Framework(name="defects4j", list_of_bugs = prog_params.d4j_list_of_bugs,
                          d4j_path=user_params.D4J_PATH, java_home=user_params.JAVA_HOME, tmp_dir=user_params.D4J_TMP_DIR,
                          validate_patch_cache_folder=prog_params.validate_patch_cache_folder,
                          n_shot_cache_folder=prog_params.n_shot_cache_folder,
                          bug_details_cache_folder=prog_params.bug_details_cache_folder)
    humanevaljava = Framework(name="humanevaljava",
                                list_of_bugs=prog_params.humaneval_list_of_bugs,
                                d4j_path=user_params.HEJ_PATH,
                                java_home=user_params.JAVA_HOME,
                                tmp_dir=user_params.HEJ_TMP_DIR,
                                validate_patch_cache_folder=prog_params.validate_patch_cache_folder,
                                n_shot_cache_folder=prog_params.n_shot_cache_folder,
                                bug_details_cache_folder=prog_params.bug_details_cache_folder)
    llm = LLM(model=model, api_key=user_params.API_KEY,
                  cache_folder=prog_params.chat_cache_folder,
                  load_from_cache=True, save_to_cache=True)
    
    frameworks = [defects4j, humanevaljava]
    if framework is not None:
        frameworks = [f for f in frameworks if f.name == framework]
    
    for test_framework in frameworks:
        ciallo = Ciallo(llm=llm, framework=test_framework)
        basellm = BaseLLM(llm=llm, framework=test_framework)
        
        aprs = [ciallo, basellm]
        if repair_tool is not None:
            aprs = [apr for apr in aprs if apr.name.lower() == repair_tool]

        for apr in aprs:
        
            if project is not None and bug_ids is not None:
                list_of_bugs_to_fix = [(project, bug_ids)]
            elif project is not None:
                if test_framework.name == "defects4j":
                    list_of_bugs_to_fix = [(project, [ids for proj, ids in prog_params.d4j_list_of_bugs if proj == project][0])]
                elif test_framework.name == "humanevaljava":
                    list_of_bugs_to_fix = [(project, [ids for proj, ids in prog_params.humaneval_list_of_bugs if proj == project][0])]
            else:
                if test_framework.name == "defects4j":
                    list_of_bugs_to_fix = prog_params.d4j_list_of_bugs
                elif test_framework.name == "humanevaljava":
                    list_of_bugs_to_fix = prog_params.humaneval_list_of_bugs
            
            analysis = Analysis(apr=apr, framework=test_framework)
            analysis.run(list_of_bugs_to_fix)


Ciallo = src.ciallo.Ciallo
#Ciallo = src.ablation.ciallo_no_direction.Ciallo
#Ciallo = src.ablation.ciallo_no_patch_sieve.Ciallo
#Ciallo = src.ablation.ciallo_no_understanding.Ciallo
if __name__ == '__main__':
    for proj, bug_ids in prog_params.d4j_list_of_bugs:
        main(framework='defects4j', project=proj, bug_ids=bug_ids, repair_tool='ciallo')
    #for proj, bug_ids in prog_params.humaneval_list_of_bugs:
    #    main(framework='humanevaljava', project=proj, bug_ids=bug_ids, repair_tool='ciallo')
